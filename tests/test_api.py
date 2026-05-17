"""
Testes automatizados para a API DuckBill AI
Sprint 4 - FIAP Challenge
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

import unittest
import json
from appClassificacao import app

class TestDuckBillAPI(unittest.TestCase):
    """Classe de testes para a API DuckBill"""
    
    def setUp(self):
        """Configuração antes de cada teste"""
        self.app = app
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True
    
    def test_home_endpoint(self):
        """Teste do endpoint raiz"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['service'], 'DuckBill AI - Classificação Inteligente de Despesas')
        self.assertIn('endpoints', data)
    
    def test_health_check(self):
        """Teste do health check"""
        response = self.client.get('/health')
        self.assertIn(response.status_code, [200, 503])
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertIn('model_loaded', data)
    
    def test_categories_endpoint(self):
        """Teste do endpoint de categorias"""
        response = self.client.get('/categories')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('categories', data)
        self.assertIsInstance(data['categories'], list)
        self.assertGreater(len(data['categories']), 0)
    
    def test_model_info_endpoint(self):
        """Teste do endpoint de informações do modelo"""
        response = self.client.get('/model-info')
        self.assertIn(response.status_code, [200, 503])
        data = json.loads(response.data)
        if response.status_code == 200:
            self.assertIn('model_type', data)
            self.assertIn('pipeline_steps', data)
    
    def test_predict_valid_input(self):
        """Teste de predição com entrada válida"""
        test_cases = [
            {"description": "McDonalds Big Mac"},
            {"description": "Netflix Monthly Subscription"},
            {"description": "Uber ride to office"},
            {"description": "Starbucks Coffee"},
            {"description": "Shell Gas Station"}
        ]
        
        for test_case in test_cases:
            response = self.client.post(
                '/predict',
                data=json.dumps(test_case),
                content_type='application/json'
            )
            
            # Pode ser 200 (sucesso) ou 503 (modelo não carregado)
            self.assertIn(response.status_code, [200, 503])
            data = json.loads(response.data)
            
            if response.status_code == 200:
                self.assertIn('category', data)
                self.assertIn('confidence', data)
                self.assertIn('status', data)
                self.assertEqual(data['status'], 'success')
                self.assertGreater(data['confidence'], 0)
                self.assertLessEqual(data['confidence'], 1)
    
    def test_predict_missing_description(self):
        """Teste de predição sem descrição"""
        response = self.client.post(
            '/predict',
            data=json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_predict_empty_description(self):
        """Teste de predição com descrição vazia"""
        response = self.client.post(
            '/predict',
            data=json.dumps({"description": ""}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_predict_short_description(self):
        """Teste de predição com descrição muito curta"""
        response = self.client.post(
            '/predict',
            data=json.dumps({"description": "a"}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_predict_long_description(self):
        """Teste de predição com descrição muito longa"""
        long_text = "a" * 501
        response = self.client.post(
            '/predict',
            data=json.dumps({"description": long_text}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_batch_predict_valid_input(self):
        """Teste de predição em lote com entrada válida"""
        test_data = {
            "descriptions": [
                "McDonalds",
                "Netflix",
                "Uber",
                "Pharmacy"
            ]
        }
        
        response = self.client.post(
            '/batch-predict',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        
        self.assertIn(response.status_code, [200, 503])
        data = json.loads(response.data)
        
        if response.status_code == 200:
            self.assertIn('results', data)
            self.assertIn('total_processed', data)
            self.assertEqual(data['total_processed'], 4)
    
    def test_batch_predict_missing_descriptions(self):
        """Teste de predição em lote sem descrições"""
        response = self.client.post(
            '/batch-predict',
            data=json.dumps({}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_batch_predict_empty_array(self):
        """Teste de predição em lote com array vazio"""
        response = self.client.post(
            '/batch-predict',
            data=json.dumps({"descriptions": []}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_batch_predict_too_many_items(self):
        """Teste de predição em lote com muitos itens"""
        test_data = {
            "descriptions": ["test"] * 101
        }
        response = self.client.post(
            '/batch-predict',
            data=json.dumps(test_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_batch_predict_invalid_type(self):
        """Teste de predição em lote com tipo inválido"""
        response = self.client.post(
            '/batch-predict',
            data=json.dumps({"descriptions": "not an array"}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_404_endpoint(self):
        """Teste de endpoint não existente"""
        response = self.client.get('/nonexistent')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_predict_special_characters(self):
        """Teste de predição com caracteres especiais"""
        test_cases = [
            {"description": "McDonald's @ 5th Avenue"},
            {"description": "Café & Bakery"},
            {"description": "Store #123"}
        ]
        
        for test_case in test_cases:
            response = self.client.post(
                '/predict',
                data=json.dumps(test_case),
                content_type='application/json'
            )
            # Deve aceitar ou retornar erro apropriado
            self.assertIn(response.status_code, [200, 400, 503])

class TestAPIIntegration(unittest.TestCase):
    """Testes de integração da API"""
    
    def setUp(self):
        """Configuração antes de cada teste"""
        self.app = app
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True
    
    def test_complete_workflow(self):
        """Teste do fluxo completo: health -> categories -> predict"""
        # 1. Verificar saúde
        health_response = self.client.get('/health')
        self.assertIn(health_response.status_code, [200, 503])
        
        # 2. Obter categorias
        categories_response = self.client.get('/categories')
        self.assertEqual(categories_response.status_code, 200)
        
        # 3. Fazer predição
        predict_response = self.client.post(
            '/predict',
            data=json.dumps({"description": "Starbucks Coffee"}),
            content_type='application/json'
        )
        self.assertIn(predict_response.status_code, [200, 503])
    
    def test_multiple_predictions_consistency(self):
        """Teste de consistência em múltiplas predições"""
        test_description = {"description": "McDonalds Big Mac"}
        
        results = []
        for _ in range(3):
            response = self.client.post(
                '/predict',
                data=json.dumps(test_description),
                content_type='application/json'
            )
            if response.status_code == 200:
                data = json.loads(response.data)
                results.append(data['category'])
        
        # Se houver resultados, todos devem ser iguais (consistência)
        if len(results) > 1:
            self.assertTrue(all(r == results[0] for r in results))

def run_tests():
    """Executa todos os testes"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestDuckBillAPI))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result

if __name__ == '__main__':
    print("=" * 70)
    print("🦆 DuckBill AI - Suite de Testes Automatizados")
    print("Sprint 4 - FIAP Challenge")
    print("=" * 70)
    print()
    
    result = run_tests()
    
    print()
    print("=" * 70)
    print(f"Testes executados: {result.testsRun}")
    print(f"Sucessos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Falhas: {len(result.failures)}")
    print(f"Erros: {len(result.errors)}")
    print("=" * 70)
    
    sys.exit(0 if result.wasSuccessful() else 1)

# Made with Bob
