import os
import sys
import unittest

from app import create_app
from models import db, User, Interview, Question
from services.pdf_service import extract_text_from_pdf
from services import gemini_service

class TestInterviewAceAI(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()

        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_user_registration_and_login(self):
        # Register user
        res = self.client.post('/register', data={
            'username': 'testcandidate',
            'email': 'test@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Welcome to InterviewAce AI', res.data)

        # Logout
        res = self.client.get('/logout', follow_redirects=True)
        self.assertIn(b'logged out safely', res.data)

        # Login
        res = self.client.post('/login', data={
            'email_or_user': 'test@example.com',
            'password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Welcome back', res.data)

    def test_invalid_session_redirection(self):
        with self.client.session_transaction() as sess:
            sess['user_id'] = 99999 # Non-existent user ID
        
        res = self.client.get('/dashboard', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'session has expired', res.data.lower())

    def test_interview_creation_and_evaluation(self):
        # Login first
        self.client.post('/register', data={
            'username': 'candidate1',
            'email': 'c1@example.com',
            'password': 'password123',
            'confirm_password': 'password123'
        })

        # Create role interview
        res = self.client.post('/api/interview/create', data={
            'interview_type': 'role',
            'role': 'Python Developer',
            'difficulty': 'Medium'
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        interview_id = data['interview_id']

        # Verify questions generated
        with self.app.app_context():
            interview = db.session.get(Interview, interview_id)
            self.assertIsNotNone(interview)
            self.assertEqual(len(interview.questions), 5)
            q1 = interview.questions[0]
            self.assertTrue(len(q1.question_text) > 0)

        # Submit answers for evaluation
        answers_payload = {}
        with self.app.app_context():
            interview = db.session.get(Interview, interview_id)
            for q in interview.questions:
                answers_payload[str(q.id)] = "In Python, memory management is handled by CPython's reference counting and garbage collection mechanisms."

        sub_res = self.client.post(f'/api/interview/{interview_id}/submit', json={'answers': answers_payload})
        self.assertEqual(sub_res.status_code, 200)
        sub_data = sub_res.get_json()
        self.assertTrue(sub_data['success'])

        # Check Report Page
        report_res = self.client.get(f'/interview/{interview_id}/report')
        self.assertEqual(report_res.status_code, 200)
        self.assertIn(b'Report', report_res.data)
        self.assertIn(b'Overall Score out of 100', report_res.data)

    def test_gemini_service_fallback(self):
        qs = gemini_service.generate_questions("Java Developer", "Hard", 5)
        self.assertEqual(len(qs), 5)
        self.assertIn("question_text", qs[0])

        eval_res = gemini_service.evaluate_interview("Java Developer", "Hard", [
            {
                "question_text": "Explain JVM Memory Structure.",
                "model_answer": "Heap and Stack.",
                "user_answer": "Heap stores objects while stack stores local variables and thread execution context."
            }
        ])
        self.assertIn("overall_score", eval_res)
        self.assertIn("summary_feedback", eval_res)
        self.assertIn("strengths", eval_res)
        self.assertIn("weaknesses", eval_res)

if __name__ == '__main__':
    unittest.main()
