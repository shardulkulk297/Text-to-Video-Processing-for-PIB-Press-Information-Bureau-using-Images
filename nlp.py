import spacy

def extract_key_points(text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    
    # Extracting key points (nouns) from the text
    key_points = [token.text for token in doc if token.pos_ == "NOUN"]

    return key_points

if __name__ == "__main__":
    # Example text (you can replace this with your actual news text)
    news_text = """
    In a groundbreaking discovery, scientists have found evidence of life on Mars. The Mars rover
    collected samples from the surface and identified organic compounds. The discovery raises
    questions about the possibility of extraterrestrial life.
    """
    
    # Extract key points
    key_points = extract_key_points(news_text)

    # Print key points
    print("Key Points:")
    print(key_points)
