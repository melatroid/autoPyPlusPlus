"""
main.py

This is a simple example module for testing without a GUI.
"""

def main():
    """
    Main function of the program.

    Prints a success message and waits for the user to press Enter before exiting.
    """
    result = " Without a gui - test successfully"  # Result message to be printed
    print(f"{result}")

    input("\nPress to end...")  # Wait for user input before ending

if __name__ == "__main__":
    main()
