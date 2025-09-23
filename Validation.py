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

    def extract_numerical_claims(self, text: str) -> List[Dict[str, Any]]:
        """
        Extracts numerical claims from text that can be validated.
        Returns a list of tuples: (extracted_value, context)
        """
        # Pattern to find numbers, percentages, and monetary values
        patterns = [
            # Currency patterns (handle commas)
            (r'\$([0-9,]+(?:\.[0-9]{2})?)', 'currency'),

            (r'(m?ROI)\s*(?:of|at|:|is)?\s*\*?\*?(\d+\.?\d*)\*?\*?', 'roi_metric'),
            
            # Percentage patterns
            (r'(\d+\.?\d*)\s*%', 'percentage'),
            
            # Saturation/performance metrics
            (r'(saturation|saturated).*?(\d+\.?\d*)\s*%', 'saturation'),
            
            # Basic numbers (but avoid list markers)
            (r'(?<!\$)(\d+\.?\d+)', 'number')
            ]
        
        proccessed_num = set()
        
        claims = []
        for pattern, claim_type in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE|re.MULTILINE)
            for match in matches:

                if len(match.groups()) >=2:
                    number_str = match.group(2)
                    prefix = match.group(1)
                elif len(match.groups()) == 1:
                    number_str = match.group(1)
                    prefix = ""
                else:
                    continue
                
                if self._is_list_number(number_str, text, match.start()):
                    continue  

                try:
                    clean_number = number_str.replace(',', '').replace('$', '')
                    raw_number = float(clean_number)

                    number_key = (raw_number, claim_type)
                    if number_key in proccessed_num:
                        continue
                    proccessed_num.add(number_key)

                except ValueError:
                    continue

                # Get context around the match
                start_pos = max(0, match.start() - 80)
                end_pos = min(len(text), match.end() + 80)
                context = text[start_pos:end_pos].strip()

                claims.append({
                    'display_value': match.group(0),  # Full matched text for display
                    'raw_number': raw_number,         # Clean number for validation
                    'context': context,
                    'claim_type': claim_type,
                    'prefix': prefix,
                    'position': match.start()
                })
    
        return claims
    
    def _is_list_marker(self, number_str: str, full_text: str, position: int) -> bool:
        """
        Better detection of list markers like "1.", "2.", "3."
        """
        # Check if it's a single digit followed by period and space/newline
        if len(number_str) == 1 and number_str.isdigit():
            # Look at what comes right after this number in the full text
            end_pos = position + len(number_str)
            if end_pos < len(full_text):
                next_chars = full_text[end_pos:end_pos + 10]
                # List markers are usually followed by ". " or ".\n" then text
                if re.match(r'^\.\s+[A-Z]', next_chars):
                    return True
        return False
    
    def _is_list_number(self, number_str: str, full_text: str, position: int) -> bool:
        """
        Fixed version that matches your calling pattern
        """
        return self._is_list_marker(number_str, full_text, position)
    
    def validate_claims(self, claims: List[Dict], source_data: Dict) -> Dict[str, Any]:
        """
        Improved validation that handles the cleaned numbers
        """
        validation_results = {
            "total_claims": len(claims),
            "verified": 0,
            "unverified": 0,
            "errors": [],
            "warnings": [],
            "verified_claims": []
        }

        # Convert the entire source data to string for pattern matching
        source_numbers = self._extract_source_numbers(source_data)

        for claim in claims:
            raw_number = claim["raw_number"]

            found_match = False 
            for source_num in source_numbers:
                if abs(raw_number - source_num) < 0.001:
                    validation_results["verified"] += 1
                    validation_results["verified_claims"].append({
                        "display_value": claim['display_value'],
                        "raw_number": raw_number,
                        "matched_source": source_num,
                        "context": claim['context'][:100] + "..." if len(claim['context']) > 100 else claim['context']
                    })
                    found_match = True
                    break
            if not found_match:
                validation_results["unverified"] += 1
                validation_results["errors"].append({
                    "display_value": claim['display_value'],
                    "raw_number": raw_number,
                    "context": claim['context'][:100] + "..." if len(claim['context']) > 100 else claim['context'],
                    "message" :"Number not found in source data"
                })

        if validation_results["total_claims"] > 0:
            validation_results["success_rate"] = validation_results["verified"] / validation_results["total_claims"]
        else:
            validation_results["success_rate"] = 0.0

        validation_results["valid"] = validation_results["success_rate"] > 0.7
        return validation_results
    
    def _extract_source_numbers(self, source_data: Dict) -> List[float]:
        """
        Extract all numerical values from source data for comparison
        """
        numbers = []
        
        def extract_recursive(obj):
            if isinstance(obj, dict):
                for value in obj.values():
                    extract_recursive(value)
            elif isinstance(obj, list):
                for item in obj:
                    extract_recursive(item)
            elif isinstance(obj, (int, float)):
                numbers.append(float(obj))
                if 0< obj < 1:
                    numbers.append(round(obj * 100, 2)) 
            elif isinstance(obj, str):
                # Try to extract numbers from strings too
                string_numbers = re.findall(r'\d+\.?\d*', obj)
                for num_str in string_numbers:
                    try:
                        numbers.append(float(num_str))
                    except ValueError:
                        pass
        
        extract_recursive(source_data)
        return numbers
    def extract_channel_name(self,question:str, source_data:Dict) -> Optional[str]:
        """
        Try to detect the channel name from the user question if not provided.
        """
        question_lower = question.lower()
        for ch in source_data.get('channels', []):
            if ch['name'].lower() in question_lower or ch['id'].lower() in question_lower:
                return ch['name']
        return None

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

        if not channel_name:
            channel_name = self.extract_channel_name(user_question, source_data)
        
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

