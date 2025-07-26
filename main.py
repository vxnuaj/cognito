#!/usr/bin/env python3
"""
Cognito - Multi-Agent Research Paper Summarization System
"""
import os
import sys
import argparse
import logging
import re
from datetime import datetime
import threading
import time

from agents.research_orchestrator import ResearchOrchestrator
from config import ANTHROPIC_API_KEY, OUTPUT_DIR, LOG_DIR
from utils.cognito_thoughts import system_thoughts, CognitoThoughts

# Configure logging
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, 'cognito.log')),
        logging.StreamHandler()
    ]
)

def validate_topic(topic: str) -> bool:
    """Validate research topic input."""
    # Check length
    if len(topic) < 3 or len(topic) > 200:
        return False
    
    # Check for valid characters (alphanumeric, spaces, hyphens, parentheses)
    if not re.match(r'^[a-zA-Z0-9\s\-\(\)]+$', topic):
        return False
    
    return True

def validate_arguments(args):
    """Validate all CLI arguments."""
    errors = []
    
    # Validate topic
    if not validate_topic(args.topic):
        errors.append("Invalid topic: Must be 3-200 characters, alphanumeric with spaces/hyphens/parentheses only")
    
    # Validate number of papers
    if args.num_papers < 1 or args.num_papers > 20:
        errors.append("Number of papers must be between 1 and 20")
    
    # Validate number of VMs
    if args.num_vms < 1 or args.num_vms > 10:
        errors.append("Number of VMs must be between 1 and 10")
    
    # Logical constraint: papers <= VMs
    if args.num_papers > args.num_vms:
        errors.append(f"Number of papers ({args.num_papers}) cannot exceed number of VMs ({args.num_vms})")
    
    return errors

def monitor_thoughts_file(thoughts_file: str, stop_event: threading.Event):
    """Monitor thoughts file and print new lines in real-time."""
    try:
        with open(thoughts_file, 'r') as f:
            # Move to end of file
            f.seek(0, 2)
            
            while not stop_event.is_set():
                line = f.readline()
                if line:
                    # Print with special formatting for CLI
                    print(f"\033[90m{line.rstrip()}\033[0m")  # Gray color for thoughts
                else:
                    time.sleep(0.1)  # Small delay when no new content
                    
    except FileNotFoundError:
        # File might not exist yet, wait for it
        while not stop_event.is_set() and not os.path.exists(thoughts_file):
            time.sleep(0.5)
        if not stop_event.is_set():
            monitor_thoughts_file(thoughts_file, stop_event)
    except Exception as e:
        logging.error(f"Error monitoring thoughts: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Cognito - Multi-agent system for comprehensive research paper analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "transformer architectures"
  python main.py "quantum computing applications" --num-papers 5
  python main.py "machine learning" --num-papers 3 --num-vms 3 --no-thoughts
        """
    )
    
    parser.add_argument(
        "topic", 
        type=str,
        help="Research topic to analyze (e.g., 'transformer architectures')"
    )
    parser.add_argument(
        "--num-papers", 
        type=int, 
        default=3,
        help="Number of papers to analyze (default: 3, max: 20)"
    )
    parser.add_argument(
        "--num-vms", 
        type=int, 
        default=3,
        help="Number of concurrent VMs to use (default: 3, max: 10)"
    )
    parser.add_argument(
        "--no-thoughts",
        action="store_true",
        help="Disable real-time thoughts streaming"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    errors = validate_arguments(args)
    if errors:
        print("❌ Invalid arguments:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    
    # Check API key
    if not ANTHROPIC_API_KEY:
        print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
        print("Please set your Anthropic API key:")
        print("  export ANTHROPIC_API_KEY='your-api-key-here'")
        sys.exit(1)
    
    # Log start
    system_thoughts.step("System Startup", f"Cognito v1.0 - Topic: {args.topic}")
    system_thoughts.analyze(f"Configuration: {args.num_papers} papers, {args.num_vms} VMs")
    
    print("🚀 Starting Cognito Research System")
    print(f"📝 Topic: {args.topic}")
    print(f"📚 Papers: {args.num_papers}")
    print(f"💻 VMs: {args.num_vms}")
    print("-" * 50)
    
    # Start thoughts monitoring in background thread (if enabled)
    stop_event = threading.Event()
    thoughts_thread = None
    
    if not args.no_thoughts:
        # Use centralized thoughts file
        thoughts_file = CognitoThoughts.get_thoughts_file()
        os.makedirs(os.path.dirname(thoughts_file), exist_ok=True)
        
        print("💭 Streaming agent thoughts...")
        print("-" * 50)
        
        thoughts_thread = threading.Thread(
            target=monitor_thoughts_file,
            args=(thoughts_file, stop_event),
            daemon=True
        )
        thoughts_thread.start()
    
    try:
        # Create output directory
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        # Initialize and run orchestrator
        orchestrator = ResearchOrchestrator()
        
        start_time = datetime.now()
        system_thoughts.step("Research Pipeline", "Starting analysis")
        
        meta_report = orchestrator.run(
            research_topic=args.topic,
            num_papers=args.num_papers,
            num_vms=args.num_vms
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        system_thoughts.success(f"Research completed in {duration:.1f} seconds")
        
        print("-" * 50)
        print(f"✅ Research completed in {duration:.1f} seconds")
        print(f"📄 Reports saved to: {OUTPUT_DIR}")
        
        # Show meta report location
        report_filename = f"{args.topic.replace(' ', '_')}_meta_report.md"
        print(f"📊 Meta report: {os.path.join(OUTPUT_DIR, report_filename)}")
        
    except KeyboardInterrupt:
        print("\n⚠️ Research interrupted by user")
        system_thoughts.error("User interrupted", "KeyboardInterrupt received")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        logging.exception("Fatal error in main")
        system_thoughts.error(f"Fatal error: {str(e)}", "See logs for details")
        sys.exit(1)
    finally:
        # Stop thoughts monitoring
        if thoughts_thread:
            stop_event.set()
            thoughts_thread.join(timeout=1)
        
        # Close system thoughts
        system_thoughts.close()

if __name__ == "__main__":
    main()