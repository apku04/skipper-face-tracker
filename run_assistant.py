#!/usr/bin/env python3
"""
Skipper Voice Assistant - Main Entry Point
Run this script to start the full AI voice assistant robot.
"""

if __name__ == "__main__":
    import sys
    import os
    
    # Get the directory containing this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    
    # Add parent to path so we can import 'skipper' as a package
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    # Change the imports in main.py to work
    # We'll just run it directly with sys.path set correctly
    main_file = os.path.join(script_dir, 'main.py')
    
    # Read and execute main.py with modified namespace
    with open(main_file, 'r') as f:
        code = f.read()
    
    # Replace relative imports with absolute ones for execution
    code = code.replace('from .', 'from ')
    
    try:
        exec(compile(code, main_file, 'exec'))
    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
