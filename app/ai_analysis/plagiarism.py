from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import PyPDF2
import docx
import re
from typing import List, Dict

class PlagiarismDetector:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            max_features=10000,
            stop_words='english',
            ngram_range=(1, 3),
            lowercase=True
        )
    
    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text from uploaded files"""
        try:
            if file_path.endswith('.pdf'):
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ''
                    for page in reader.pages:
                        text += page.extract_text()
                    return text
            elif file_path.endswith('.docx'):
                doc = docx.Document(file_path)
                return ' '.join([p.text for p in doc.paragraphs])
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except:
            return ''
    
    def preprocess_text(self, text: str) -> str:
        """Clean text"""
        text = text.lower()
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        text = ' '.join(text.split())
        return text
    
    def detect_plagiarism(self, text: str, corpus: List[str]) -> Dict:
        """Detect plagiarism"""
        processed_text = self.preprocess_text(text)
        
        if not processed_text or len(processed_text) < 50:
            return {
                'plagiarism_score': 0,
                'top_matches': [],
                'total_matches': 0,
                'status': 'low_risk'
            }
        
        # Combine with corpus
        all_texts = [processed_text] + [self.preprocess_text(doc) for doc in corpus]
        
        try:
            vectors = self.vectorizer.fit_transform(all_texts)
            similarities = cosine_similarity(vectors[0:1], vectors[1:])
            
            # Find matches
            top_matches = []
            for idx, sim in enumerate(similarities[0]):
                if sim > 0.1:
                    top_matches.append({
                        'document_index': idx,
                        'similarity_score': sim * 100,
                        'match_percentage': sim * 100
                    })
            
            top_matches.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            # Calculate score
            plagiarism_score = max([m['similarity_score'] for m in top_matches]) if top_matches else 0
            
            return {
                'plagiarism_score': plagiarism_score,
                'top_matches': top_matches[:5],
                'total_matches': len(top_matches),
                'status': 'high_risk' if plagiarism_score > 60 else 'medium_risk' if plagiarism_score > 30 else 'low_risk'
            }
        except:
            return {
                'plagiarism_score': 0,
                'top_matches': [],
                'total_matches': 0,
                'status': 'low_risk'
            }