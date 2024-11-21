import random
import re
from typing import Optional, Dict, List

class AIUtils:
    def __init__(self):
        self.conversation_history = []
        self.question_patterns = {}
        self.success_rate = {}
        self.disqualification_phrases = set()
        self.persona = self._generate_persona()

    def _generate_persona(self) -> Dict[str, str]:
        """Generate a consistent persona for survey responses."""
        age_ranges = [(25, 34), (35, 44), (45, 54)]
        selected_range = random.choice(age_ranges)
        age = random.randint(selected_range[0], selected_range[1])
        
        occupations = [
            "Software Engineer", "Product Manager", "Data Analyst",
            "Marketing Manager", "Business Analyst", "Project Manager"
        ]
        
        education_levels = [
            "Bachelor's Degree", "Master's Degree",
            "Some College", "Associate's Degree"
        ]
        
        income_ranges = [
            "50,000 - 74,999", "75,000 - 99,999",
            "100,000 - 124,999", "125,000 - 149,999"
        ]
        
        locations = [
            "San Francisco, CA", "Seattle, WA", "Austin, TX",
            "Boston, MA", "Denver, CO", "Chicago, IL"
        ]
        
        return {
            "age": age,
            "occupation": random.choice(occupations),
            "education": random.choice(education_levels),
            "income": random.choice(income_ranges),
            "location": random.choice(locations),
            "interests": self._generate_interests()
        }

    def _generate_interests(self) -> List[str]:
        """Generate a consistent set of interests."""
        all_interests = [
            "Technology", "Travel", "Fitness", "Reading",
            "Cooking", "Photography", "Gaming", "Hiking",
            "Music", "Movies", "Art", "Sports"
        ]
        
        # Select 3-5 interests
        num_interests = random.randint(3, 5)
        return random.sample(all_interests, num_interests)

    def get_question_text(self, element) -> Optional[str]:
        """Extract question text from an element and its surrounding context."""
        try:
            # Try to find question text in common locations
            selectors = [
                '.question-text', '.question-title', '.question-label',
                'label', 'legend', '[role="heading"]', 'h1', 'h2', 'h3',
                '[class*="question"]', '[class*="title"]', '[class*="label"]'
            ]
            
            for selector in selectors:
                try:
                    question_element = element.find_element_by_css_selector(selector)
                    if question_element:
                        text = question_element.text.strip()
                        if text:
                            return text
                except:
                    continue
            
            # If no specific question element found, try getting text from parent
            text = element.text.strip()
            if text:
                # Try to extract the first sentence or line
                sentences = re.split(r'[.!?\n]', text)
                if sentences:
                    return sentences[0].strip()
            
            return None
            
        except Exception as e:
            print(f"Error getting question text: {str(e)}")
            return None

    def get_response(self, question: str) -> Optional[str]:
        """Get AI-generated response for a survey question with enhanced learning."""
        try:
            # Check for similar questions in history
            similar_question = self._find_similar_questions(question)
            if similar_question and similar_question in self.success_rate:
                if self.success_rate[similar_question] > 0.7:
                    return self.question_patterns[similar_question]
            
            # Generate response based on question type
            if self._is_demographic_question(question):
                return self._get_demographic_response(question)
            elif self._is_opinion_question(question):
                return self._get_opinion_response(question)
            elif self._is_frequency_question(question):
                return self._get_frequency_response(question)
            else:
                return self._get_generic_response(question)
            
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return None

    def _is_demographic_question(self, question: str) -> bool:
        """Check if question is asking for demographic information."""
        demographic_keywords = [
            'age', 'gender', 'income', 'education', 'occupation',
            'marital status', 'ethnicity', 'location', 'household'
        ]
        return any(keyword in question.lower() for keyword in demographic_keywords)

    def _is_opinion_question(self, question: str) -> bool:
        """Check if question is asking for an opinion."""
        opinion_keywords = [
            'think', 'feel', 'believe', 'opinion', 'prefer',
            'like', 'dislike', 'agree', 'disagree'
        ]
        return any(keyword in question.lower() for keyword in opinion_keywords)

    def _is_frequency_question(self, question: str) -> bool:
        """Check if question is asking about frequency."""
        frequency_keywords = [
            'how often', 'frequency', 'regularly', 'times per',
            'daily', 'weekly', 'monthly', 'yearly'
        ]
        return any(keyword in question.lower() for keyword in frequency_keywords)

    def _get_demographic_response(self, question: str) -> str:
        """Generate response for demographic questions based on persona."""
        question = question.lower()
        if 'age' in question:
            return str(self.persona['age'])
        elif 'occupation' in question:
            return self.persona['occupation']
        elif 'education' in question:
            return self.persona['education']
        elif 'income' in question:
            return self.persona['income']
        elif 'location' in question or 'live' in question:
            return self.persona['location']
        else:
            return self._get_generic_response(question)

    def _get_opinion_response(self, question: str) -> str:
        """Generate consistent opinion responses."""
        # Use interests to influence opinions
        relevant_interests = [
            interest for interest in self.persona['interests']
            if interest.lower() in question.lower()
        ]
        
        if relevant_interests:
            return f"Strongly interested in {relevant_interests[0]}"
        
        # Generate random but consistent opinion
        response_seed = hash(question + str(self.persona['age']))
        random.seed(response_seed)
        
        options = ["Somewhat agree", "Agree", "Strongly agree", "Neutral", 
                  "Somewhat disagree", "Disagree", "Strongly disagree"]
        weights = [0.2, 0.3, 0.2, 0.15, 0.05, 0.05, 0.05]
        
        return random.choices(options, weights=weights)[0]

    def _get_frequency_response(self, question: str) -> str:
        """Generate consistent frequency responses."""
        response_seed = hash(question + str(self.persona['age']))
        random.seed(response_seed)
        
        if 'daily' in question.lower():
            return str(random.randint(1, 5)) + " times per day"
        elif 'weekly' in question.lower():
            return str(random.randint(1, 7)) + " times per week"
        elif 'monthly' in question.lower():
            return str(random.randint(1, 8)) + " times per month"
        else:
            frequencies = ["Rarely", "Sometimes", "Often", "Very often"]
            weights = [0.2, 0.4, 0.3, 0.1]
            return random.choices(frequencies, weights=weights)[0]

    def _get_generic_response(self, question: str) -> str:
        """Generate generic response when question type is unclear."""
        response_seed = hash(question + str(self.persona['age']))
        random.seed(response_seed)
        return str(random.randint(1, 5))  # Default to 1-5 scale

    def _find_similar_questions(self, question: str) -> Optional[str]:
        """Find similar questions from history using text similarity."""
        try:
            question = question.lower()
            best_match = None
            highest_similarity = 0.6  # Minimum similarity threshold
            
            for past_question in self.question_patterns:
                similarity = self._calculate_similarity(question, past_question.lower())
                if similarity > highest_similarity:
                    highest_similarity = similarity
                    best_match = past_question
            
            return best_match
            
        except Exception as e:
            print(f"Error finding similar questions: {str(e)}")
            return None

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using a simple algorithm."""
        try:
            # Convert to sets of words
            words1 = set(text1.split())
            words2 = set(text2.split())
            
            # Calculate Jaccard similarity
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            
            return intersection / union if union > 0 else 0
            
        except Exception as e:
            print(f"Error calculating similarity: {str(e)}")
            return 0

    def update_learning(self, question: str, success: bool) -> None:
        """Update success rates and patterns based on survey results."""
        try:
            if question not in self.success_rate:
                self.success_rate[question] = 1.0 if success else 0.0
                if success:
                    self.question_patterns[question] = self.get_response(question)
            else:
                # Update success rate with exponential moving average
                alpha = 0.3
                current_rate = self.success_rate[question]
                self.success_rate[question] = (alpha * (1.0 if success else 0.0) + 
                                             (1 - alpha) * current_rate)
                
                # Update pattern if successful
                if success and question in self.question_patterns:
                    self.question_patterns[question] = self.get_response(question)
                    
        except Exception as e:
            print(f"Error updating learning: {str(e)}")

    def handle_disqualification(self, text: str) -> None:
        """Learn from survey disqualifications."""
        try:
            # Extract potential phrases that led to disqualification
            sentences = re.split(r'[.!?\n]', text)
            for sentence in sentences:
                sentence = sentence.strip().lower()
                if len(sentence) > 10:  # Ignore very short phrases
                    self.disqualification_phrases.add(sentence)
                    
        except Exception as e:
            print(f"Error handling disqualification: {str(e)}")
