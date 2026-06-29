#!/usr/bin/env python3
"""
Simple CLI for Groq Agent
"""

from agent.groq_agent import GroqAgent
import sys

def print_banner():
    print("\n" + "="*80)
    print("🤖 Decision AI - Groq Agent with Web Search & Database")
    print("="*80)
    print("\n💡 Examples:")
    print("  • Who is Elon Musk?")
    print("  • What is quantum computing?")
    print("  • Save this to database")
    print("  • Show my search history")
    print("  • Search for 'AI' in my history")
    print("  • Show database statistics")
    print("\n⌨️  Commands:")
    print("  • 'reset' - Clear conversation")
    print("  • 'quit' or 'exit' - Exit")
    print("="*80 + "\n")

def main():
    try:
        print_banner()
        
        # Initialize agent
        print("🔧 Initializing agent...")
        agent = GroqAgent()
        print("✅ Agent ready!\n")
        
        # Main loop
        while True:
            try:
                # Get user input
                user_input = input("💬 You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!\n")
                    sys.exit(0)
                
                if user_input.lower() == 'reset':
                    agent.reset_conversation()
                    continue
                
                if user_input.lower() == 'help':
                    print_banner()
                    continue
                
                # Run agent
                print()  # Blank line for readability
                agent.run(user_input)
                
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Goodbye!\n")
                sys.exit(0)
                
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")
    
    except ValueError as e:
        print(f"\n❌ Configuration Error: {str(e)}")
        print("\n📝 Setup Instructions:")
        print("1. Get Groq API key from: https://console.groq.com")
        print("2. Add to .env file: GROQ_API_KEY=your_key_here")
        print("3. Run: pip install groq")
        print()
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Initialization Error: {str(e)}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
