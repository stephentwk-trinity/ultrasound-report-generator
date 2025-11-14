import subprocess
import sys

def main():
    """
    Launches the Streamlit UI for the Ultrasound Report Generator.
    """
    try:
        subprocess.run([f"{sys.executable}", "-m", "streamlit", "run", "src/ui/app.py"], check=True)
    except FileNotFoundError:
        print("Error: `streamlit` is not installed. Please install it by running `pip install streamlit`")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred while launching Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()