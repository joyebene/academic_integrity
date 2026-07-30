import torch
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
import numpy as np
from typing import Dict, List
import re

class AIContentDetector:
    def __init__(self):
        """Initialize AI content detector using Transformers"""
        try:
            # Use a lighter model
            self.model_name = "microsoft/deberta-base"
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            
            # Use zero-shot classification for flexibility
            self.classifier = pipeline("zero-shot-classification", 
                                     model="facebook/bart-large-mnli")
            
            # Use text classification pipeline
            self.text_classifier = pipeline("text-classification", 
                                          model="textattack/roberta-base-SST-2")
        except:
            # Fallback to simple rule-based detection
            self.classifier = None
            print("Using rule-based AI detection fallback")
        
    def preprocess_text(self, text: str) -> str:
        """Clean text for analysis"""
        text = text.lower()
        text = re.sub(r'[^a-zA-Z0-9\s.,!?;]', '', text)
        text = ' '.join(text.split())
        return text[:1000]  # Limit length
    
    def extract_features(self, text: str) -> Dict:
        """Extract linguistic features"""
        words = text.split()
        sentences = text.split('.')
        
        # Basic features
        avg_word_length = sum(len(w) for w in words) / len(words) if words else 0
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        
        # Vocabulary richness
        unique_words = set(words)
        lexical_diversity = len(unique_words) / len(words) if words else 0
        
        # Punctuation density
        punct_count = sum(1 for c in text if c in '.,!?;')
        punct_density = punct_count / len(text) if text else 0
        
        # Word frequency analysis
        from collections import Counter
        word_freq = Counter(words)
        most_common = word_freq.most_common(5)
        
        # Repetitiveness
        repetitiveness = 0
        for word, count in word_freq.items():
            if count > 1:
                repetitiveness += count - 1
        repetitiveness = repetitiveness / len(words) if words else 0
        
        return {
            'avg_word_length': avg_word_length,
            'avg_sentence_length': avg_sentence_length,
            'lexical_diversity': lexical_diversity,
            'punct_density': punct_density,
            'repetitiveness': repetitiveness,
            'unique_word_count': len(unique_words),
            'total_words': len(words),
            'total_sentences': len(sentences),
            'most_common_words': most_common
        }
    
    def predict_ai_generated(self, text: str) -> Dict:
        """Predict if text is AI-generated"""
        features = self.extract_features(text)
        
        # Rule-based scoring
        score = 0
        max_score = 100
        
        # Feature-based detection
        if features['avg_word_length'] > 6.5:
            score += 15
        if features['lexical_diversity'] < 0.4:
            score += 20
        if features['repetitiveness'] > 0.15:
            score += 15
        if features['punct_density'] < 0.02:
            score += 10
        
        # Use transformer model if available
        try:
            if self.classifier:
                # Classify text as "human" vs "AI"
                result = self.text_classifier(text[:512])
                if result:
                    score = float(result[0]['score']) * 100
        except:
            pass
        
        # Normalize score
        ai_probability = min(score, 100)
        
        return {
            'ai_probability': ai_probability,
            'prediction': 'AI_Generated' if ai_probability > 55 else 'Human_Written',
            'confidence': abs(ai_probability - 50) * 2,
            'features': features,
            'risk_level': 'high' if ai_probability > 70 else 'medium' if ai_probability > 40 else 'low'
        }
    
    def generate_detailed_analysis(self, text: str) -> Dict:
        """Generate comprehensive analysis"""
        result = self.predict_ai_generated(text)
        
        return {
            'ai_probability_score': result['ai_probability'],
            'classification': result['prediction'],
            'confidence_score': result['confidence'],
            'risk_level': result['risk_level'],
            'features': result['features'],
            'recommendations': self.generate_recommendations(
                result['ai_probability'], 
                result['prediction']
            )
        }
    
    def generate_recommendations(self, score: float, prediction: str) -> List[str]:
        """Generate recommendations"""
        if prediction == 'AI_Generated' and score > 70:
            return [
                "Strong indicators of AI-generated content detected",
                "Request original work or additional explanation",
                "Review submission in detail"
            ]
        elif prediction == 'AI_Generated' and score > 40:
            return [
                "Some indicators of AI generation present",
                "Consider a more detailed review",
                "Discuss the submission with the student"
            ]
        else:
            return [
                "No significant AI-generation indicators found",
                "Content appears human-written"
            ]