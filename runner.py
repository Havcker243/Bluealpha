import argparse
from workflow import answer_channel_question, get_safe_spend_range, get_best_channel_by_roi, list_channels
from AI import ai_answer

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="MMM AI Workflow Runner")

    # Define arguments
    parser.add_argument("--mode", choices=["channel", "safe", "best", "ai"], required=True,
                        help="Which function to run: channel, safe, best, ai")
    
    # Additional arguments based on mode
    parser.add_argument("--name", type=str, help="Channel name (for channel/safe/ai modes)")
    parser.add_argument("--question", type=str, help="User question (for ai mode only)")
    
    args = parser.parse_args()

    # Execute based on mode
    if args.mode == "channel":
        if not args.name:
            print("Please provide --name for channel mode")
        else:
            print(answer_channel_question(args.name))

    elif args.mode == "safe":
        if not args.name:
            print("Please provide --name for safe mode")
        else:
            print(get_safe_spend_range(args.name))

    elif args.mode == "best":
        print(get_best_channel_by_roi())

    elif args.mode == "ai":
        if not args.question:
            print("Please provide --question for ai mode")
        else:
            print(ai_answer(args.question, args.name))

if __name__ == "__main__":
    main()
