from datasets import load_dataset
import os

def download_data():
    print("Downloading DeepMind Code Contests dataset...")
    # Download the dataset from Hugging Face
    dataset = load_dataset("deepmind/code_contests", split="train")
    
    print("Saving dataset to dm-code_contests/...")
    # Save to local disk in Arrow format
    dataset.save_to_disk("dm-code_contests")
    print("Done! Dataset is ready in dm-code_contests/")

if __name__ == "__main__":
    download_data()
