# validator.py (Enhanced Version)
import re
import json
from typing import Dict, Any, List, Tuple, Optional

class ResponseValidator:
    
    def __init__(self):
        # Patterns to detect specific metrics in user questions
        self.metric_patterns = {
            "roi": r"\b(roi|return on investment|return on ad spend)\b",
            "mroi": r"\b(marginal roi|mroi|incremental roi)\b",
            "contribution": r"\b(contribution|percent contribution|contributed|share)\b",
            "spend": r"\b(spend|investment|cost|budget)\b",
            "revenue": r"\b(revenue|incremental revenue|value)\b"
        }

    def extract_numerical_claims(self, text: str) -> List[Tuple[str, str]]:
        """
        Extracts numerical claims from text that can be validated.
        Returns a list of tuples: (extracted_value, context)
        """
        # Pattern to find numbers, percentages, and monetary values
        patterns = [
            r'(\$?\d+\.?\d*\%?)',  # Basic numbers, percentages, and currencies
            r'(\d+\.?\d*\s*%)',    # Percentage with space
            r'(ROI.*?\d+\.?\d*)',  # ROI claims
            r'(contribution.*?\d+\.?\d*\s*%)',  # Contribution percentages
        ]
        
        claims = []
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Get some context around the number (10 words before and after)
                match_index = text.find(match.group())
                if match_index != -1:
                    # Simple context extraction
                    start_pos = max(0, match_index - 50)
                    end_pos = min(len(text), match_index + len(match.group()) + 50)
                    context = text[start_pos:end_pos]
                    claims.append((match.group(), context))
        
        return claims
    
    def validate_claims(self, claims: List[Tuple[str, str]], source_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates extracted claims against the source data.
        """
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "verified_claims": []
        }

        # Convert the entire source data to string for pattern matching
        source_str = json.dumps(source_data)
        
        for value, context in claims:
            # Clean the extracted value for comparison
            clean_value = value.replace(' ', '').replace('%', '').replace('$', '')
            # Check if this exact value exists in source data
            if clean_value in source_str:
                validation_results["verified_claims"].append({
                    "value": value,
                    "context": context,
                    "status": "verified"
                })
            else:
                # Check if it's a percentage that might be calculated
                if '%' in value and clean_value.replace('.', '').isdigit():
                    # This might be a calculated percentage, not a direct error
                    validation_results["warnings"].append({
                        "value": value,
                        "context": context,
                        "message": "Percentage not directly found in source - may be calculated"
                    })
                else:
                    validation_results["errors"].append({
                        "value": value,
                        "context": context,
                        "message": "Value not found in source data"
                    })
                    validation_results["valid"] = False
        
        return validation_results

    def extract_metric_from_question(self, question: str) -> Optional[str]:
        """Detects which specific metric a user is asking about."""
        question_lower = question.lower()
        for metric, pattern in self.metric_patterns.items():
            if re.search(pattern, question_lower):
                return metric
        return None  # Could not detect a specific metric

    def query_source_data(self, metric: str, channel_name: str, source_data: Dict) -> Optional[float]:
        """Executes a precise query to get the true value from the source."""
        try:
            channels = source_data.get('channels', [])
            for channel in channels:
                # Check if this is the channel we're looking for
                if channel_name and (channel['name'].lower() == channel_name.lower() or 
                                   channel['id'].lower() == channel_name.lower()):
                    # Return the requested metric
                    return channel.get(metric, None)
                    
            # If no channel specified or not found, return None
            return None
        except (KeyError, TypeError):
            return None

    def validate_specific_query(self, user_question: str, ai_response: str, 
                              channel_name: str, source_data: Dict) -> Dict[str, Any]:
        """
        Enhanced validation for when we can identify a specific metric query.
        """
        # Step 1: Detect what metric the user is asking for
        target_metric = self.extract_metric_from_question(user_question)
        if not target_metric or not channel_name:
            return {"specific_validation": False, "reason": "Could not identify specific metric or channel"}
        
        # Step 2: Get the ground truth value from source data
        true_value = self.query_source_data(target_metric, channel_name, source_data)
        if true_value is None:
            return {"specific_validation": False, "reason": "Could not find metric in source data"}
        
        # Step 3: Extract all numbers from AI response
        numbers_in_response = re.findall(r'\d+\.?\d*', ai_response)
        numbers_in_response = [float(num) for num in numbers_in_response]
        
        # Step 4: Check if the true value is in the AI's response
        # Use tolerance for floating point comparison
        found = any(abs(num - true_value) < 0.01 for num in numbers_in_response)
        
        return {
            "specific_validation": True,
            "metric": target_metric,
            "channel": channel_name,
            "true_value": true_value,
            "found_in_response": found,
            "numbers_in_response": numbers_in_response
        }
    

    def validate_ranking(self, ai_response: str, ranking_metric: str, source_data: Dict) -> Dict[str, Any]:
        """
        Validates a ranking answer (e.g., 'top 5 channels by ROI') by performing
        the same sorting operation on the source data and comparing results.
        """
        # Step 1: Extract the list of channels mentioned from the AI response
        mentioned_channels = []
        # Simple approach: look for channel names in the response
        for channel in source_data.get('channels', []):
            if channel['name'].lower() in ai_response.lower():
                mentioned_channels.append(channel['name'])

        # Step 2: Manually compute the actual ranking from the source data
        all_channels = source_data.get('channels', [])
        # Sort channels by the specified metric (e.g., 'roi') in descending order
        try:
            truly_top_channels = sorted(all_channels, 
                                      key=lambda x: x.get(ranking_metric, 0), 
                                      reverse=True)
            truly_top_names = [ch['name'] for ch in truly_top_channels]
        except KeyError:
            return {"validation_type": "ranking", "valid": False, "error": f"Metric '{ranking_metric}' not found in data"}

        # Step 3: Compare the AI's list with our computed list
        # We don't expect perfect match due to text formatting, but the top N should be similar
        ai_list = mentioned_channels  # This is a crude approximation
        overlap = set(ai_list) & set(truly_top_names[:len(ai_list)])

        return {
            "validation_type": "ranking",
            "metric": ranking_metric,
            "ai_mentioned_channels": ai_list,
            "true_top_5_channels": truly_top_names[:5],
            "overlap_count": len(overlap),
            "is_plausible": len(overlap) >= 3  # e.g., If at least 3 of the top 5 match, it's plausible
        }
    
    # validator.py (Master validation method)
    def validate_adaptive(self, ai_response: str, source_data: Dict, user_question: str, channel_name:str = "") -> Dict[str, Any]:
        """
        Chooses the right validation strategy based on the type of question.
        """
        # 1. Check if it's a specific metric query (e.g., "what is the roi of google?")
        target_metric = self.extract_metric_from_question(user_question)
        if target_metric:
            result = self.validate_specific_query(user_question, ai_response, channel_name, source_data)
            result["strategy"] = "specific_metric"
            return result

        # 2. Check if it's a ranking question (e.g., "top channels", "worst performing")
        ranking_metrics = ['roi', 'mroi', 'contribution_pct', 'spend']
        for metric in ranking_metrics:
            if metric in user_question.lower() or any(word in user_question.lower() for word in ["top", "best", "worst", "lowest"]):
                result = self.validate_ranking(ai_response, metric, source_data)
                result["strategy"] = "ranking"
                return result

        # 3. Default: General fact-checking of all numbers
        result = self.validate_claims(self.extract_numerical_claims(ai_response), source_data)
        result["strategy"] = "general_fact_check"
        return result
    
    
    def validate_response(self, ai_response: str, source_data: Dict, 
                         user_question: str = "", channel_name: str = "") -> Dict[str, Any]:
        """
        Main validation method - uses adaptive strategy by default.
        """
        adaptive_result = self.validate_adaptive(ai_response, source_data, user_question, channel_name)
        
        # Also run general validation for comprehensive checking
        claims = self.extract_numerical_claims(ai_response)
        general_validation = self.validate_claims(claims, source_data)
        
        return {
            "adaptive_validation": adaptive_result,
            "general_validation": general_validation,
            "overall_valid": general_validation["valid"] and adaptive_result.get("valid", True)
        }

