import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer
import re
from collections import Counter
from typing import List, Dict, Tuple

class NLPUtils:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.download_nltk_data()
    
    def download_nltk_data(self):
        """Download required NLTK data"""
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
            nltk.data.find('corpora/wordnet')
        except LookupError:
            nltk.download('punkt')
            nltk.download('stopwords')
            nltk.download('wordnet')
    
    def tokenize_words(self, text: str) -> List[str]:
        """Tokenize text into words"""
        return word_tokenize(text.lower())
    
    def tokenize_sentences(self, text: str) -> List[str]:
        """Tokenize text into sentences"""
        return sent_tokenize(text)
    
    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        """Remove stopwords from token list"""
        return [token for token in tokens if token not in self.stop_words]
    
    def lemmatize_tokens(self, tokens: List[str]) -> List[str]:
        """Lemmatize tokens"""
        return [self.lemmatizer.lemmatize(token) for token in tokens]
    
    def get_word_frequencies(self, text: str) -> Dict[str, int]:
        """Get word frequency distribution"""
        tokens = self.tokenize_words(text)
        tokens = self.remove_stopwords(tokens)
        tokens = self.lemmatize_tokens(tokens)
        return dict(Counter(tokens))
    
    def get_ngrams(self, text: str, n: int = 3) -> List[Tuple[str, ...]]:
        """Extract n-grams from text"""
        tokens = self.tokenize_words(text)
        tokens = self.remove_stopwords(tokens)
        tokens = self.lemmatize_tokens(tokens)
        
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngrams.append(tuple(tokens[i:i+n]))
        
        return ngrams
    
    def get_most_frequent_ngrams(self, text: str, n: int = 3, top_n: int = 10) -> List[Tuple[Tuple[str, ...], int]]:
        """Get most frequent n-grams"""
        ngrams = self.get_ngrams(text, n)
        ngram_counts = Counter(ngrams)
        return ngram_counts.most_common(top_n)
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """Extract keywords from text"""
        word_freq = self.get_word_frequencies(text)
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:top_n]]
    
    def calculate_readability_score(self, text: str) -> float:
        """Calculate Flesch Reading Ease score"""
        sentences = self.tokenize_sentences(text)
        words = self.tokenize_words(text)
        syllables = self.count_syllables(text)
        
        if len(sentences) == 0 or len(words) == 0:
            return 0
        
        # Flesch Reading Ease Formula
        score = 206.835 - 1.015 * (len(words) / len(sentences)) - 84.6 * (syllables / len(words))
        return max(0, min(100, score))  # Clamp between 0 and 100
    
    def count_syllables(self, text: str) -> int:
        """Count syllables in text"""
        text = text.lower()
        vowels = "aeiouy"
        count = 0
        
        for word in text.split():
            word_count = 0
            prev_char = ""
            for char in word:
                if char in vowels and prev_char not in vowels:
                    word_count += 1
                prev_char = char
            
            if word.endswith('e'):
                word_count -= 1
            
            if word_count == 0:
                word_count = 1
            
            count += word_count
        
        return count
    
    def generate_text_summary(self, text: str, num_sentences: int = 3) -> str:
        """Generate a summary of the text"""
        sentences = self.tokenize_sentences(text)
        
        if len(sentences) <= num_sentences:
            return ' '.join(sentences)
        
        # Score sentences based on word frequency
        word_freq = self.get_word_frequencies(text)
        sentence_scores = {}
        
        for sentence in sentences:
            sentence_tokens = self.tokenize_words(sentence)
            score = sum(word_freq.get(token, 0) for token in sentence_tokens)
            sentence_scores[sentence] = score
        
        # Get top sentences
        sorted_sentences = sorted(sentence_scores.items(), key=lambda x: x[1], reverse=True)
        top_sentences = [sentence for sentence, _ in sorted_sentences[:num_sentences]]
        
        return ' '.join(top_sentences)
    
    def detect_writing_style_anomalies(self, text: str) -> Dict[str, float]:
        """Detect writing style anomalies"""
        sentences = self.tokenize_sentences(text)
        words = self.tokenize_words(text)
        
        # Calculate sentence length variability
        sentence_lengths = [len(sent.split()) for sent in sentences]
        avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0
        max_sentence_length = max(sentence_lengths) if sentence_lengths else 0
        min_sentence_length = min(sentence_lengths) if sentence_lengths else 0
        
        # Calculate vocabulary richness
        unique_words = set(words)
        lexical_diversity = len(unique_words) / len(words) if words else 0
        
        # Calculate readability
        readability_score = self.calculate_readability_score(text)
        
        return {
            'avg_sentence_length': avg_sentence_length,
            'sentence_length_variability': max_sentence_length - min_sentence_length if sentence_lengths else 0,
            'lexical_diversity': lexical_diversity,
            'readability_score': readability_score,
            'total_sentences': len(sentences),
            'total_words': len(words),
            'unique_words': len(unique_words)
        }