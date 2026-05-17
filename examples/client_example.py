"""
Exemplo de cliente Python para a API DuckBill AI
Demonstra como integrar a API em aplicações Python
Sprint 4 - FIAP Challenge
"""

import requests
import json
from typing import Dict, List, Optional

class DuckBillClient:
    """Cliente Python para a API DuckBill AI"""
    
    def __init__(self, base_url: str = "http://localhost:5000"):
        """
        Inicializa o cliente
        
        Args:
            base_url: URL base da API (padrão: http://localhost:5000)
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
    
    def health_check(self) -> Dict:
        """
        Verifica o status da API
        
        Returns:
            Dict com informações de saúde da API
        """
        response = self.session.get(f"{self.base_url}/health")
        return response.json()
    
    def get_categories(self) -> List[str]:
        """
        Obtém lista de categorias disponíveis
        
        Returns:
            Lista de categorias
        """
        response = self.session.get(f"{self.base_url}/categories")
        data = response.json()
        return data.get('categories', [])
    
    def get_model_info(self) -> Dict:
        """
        Obtém informações sobre o modelo de IA
        
        Returns:
            Dict com informações do modelo
        """
        response = self.session.get(f"{self.base_url}/model-info")
        return response.json()
    
    def predict(self, description: str) -> Dict:
        """
        Classifica uma única descrição de gasto
        
        Args:
            description: Descrição do gasto
            
        Returns:
            Dict com categoria, confiança e outras informações
        """
        payload = {"description": description}
        response = self.session.post(
            f"{self.base_url}/predict",
            data=json.dumps(payload)
        )
        response.raise_for_status()
        return response.json()
    
    def batch_predict(self, descriptions: List[str]) -> Dict:
        """
        Classifica múltiplas descrições de gastos
        
        Args:
            descriptions: Lista de descrições
            
        Returns:
            Dict com resultados de todas as predições
        """
        payload = {"descriptions": descriptions}
        response = self.session.post(
            f"{self.base_url}/batch-predict",
            data=json.dumps(payload)
        )
        response.raise_for_status()
        return response.json()
    
    def close(self):
        """Fecha a sessão HTTP"""
        self.session.close()


def exemplo_uso_basico():
    """Exemplo básico de uso do cliente"""
    print("=" * 70)
    print("🦆 DuckBill AI - Exemplo de Uso Básico")
    print("=" * 70)
    print()
    
    # Criar cliente
    client = DuckBillClient()
    
    try:
        # 1. Verificar saúde da API
        print("1. Verificando saúde da API...")
        health = client.health_check()
        print(f"   Status: {health.get('status')}")
        print(f"   Modelo carregado: {health.get('model_loaded')}")
        print()
        
        # 2. Obter categorias disponíveis
        print("2. Categorias disponíveis:")
        categories = client.get_categories()
        for cat in categories[:5]:  # Mostrar apenas 5
            print(f"   - {cat}")
        print(f"   ... e mais {len(categories) - 5} categorias")
        print()
        
        # 3. Classificar uma única descrição
        print("3. Classificando uma descrição:")
        description = "McDonalds Big Mac"
        result = client.predict(description)
        print(f"   Descrição: {result.get('description')}")
        print(f"   Categoria: {result.get('category')}")
        print(f"   Confiança: {result.get('confidence'):.2%}")
        print()
        
        # 4. Mostrar top 3 predições
        if 'top_predictions' in result:
            print("   Top 3 categorias mais prováveis:")
            for pred in result['top_predictions']:
                print(f"   - {pred['category']}: {pred['confidence']:.2%}")
        print()
        
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar à API.")
        print("   Certifique-se de que o servidor está rodando em http://localhost:5000")
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        client.close()


def exemplo_batch_prediction():
    """Exemplo de predição em lote"""
    print("=" * 70)
    print("🦆 DuckBill AI - Exemplo de Predição em Lote")
    print("=" * 70)
    print()
    
    client = DuckBillClient()
    
    try:
        # Lista de gastos para classificar
        gastos = [
            "Starbucks Coffee",
            "Netflix Monthly Subscription",
            "Uber ride to airport",
            "Shell Gas Station",
            "Amazon Prime Video",
            "Pharmacy CVS",
            "Nike Running Shoes",
            "Whole Foods Market"
        ]
        
        print(f"Classificando {len(gastos)} gastos...")
        print()
        
        # Fazer predição em lote
        result = client.batch_predict(gastos)
        
        print(f"Total processado: {result.get('total_processed')}")
        print(f"Sucessos: {result.get('successful')}")
        print(f"Falhas: {result.get('failed')}")
        print()
        
        # Mostrar resultados
        print("Resultados:")
        print(f"{'Descrição':<30} | {'Categoria':<20} | {'Confiança'}")
        print("-" * 70)
        
        for item in result.get('results', []):
            desc = item['description'][:28]
            cat = item['category'][:18]
            conf = item['confidence']
            print(f"{desc:<30} | {cat:<20} | {conf:.2%}")
        
        # Mostrar erros se houver
        if result.get('errors'):
            print()
            print("Erros encontrados:")
            for error in result['errors']:
                print(f"  - {error['description']}: {error['error']}")
        
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar à API.")
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        client.close()


def exemplo_integracao_sistema():
    """Exemplo de integração com sistema de gestão financeira"""
    print("=" * 70)
    print("🦆 DuckBill AI - Exemplo de Integração com Sistema")
    print("=" * 70)
    print()
    
    client = DuckBillClient()
    
    try:
        # Simular transações bancárias vindas de um sistema
        transacoes = [
            {"id": 1, "data": "2024-05-01", "descricao": "UBER *TRIP", "valor": 25.50},
            {"id": 2, "data": "2024-05-02", "descricao": "NETFLIX.COM", "valor": 39.90},
            {"id": 3, "data": "2024-05-03", "descricao": "MCDONALDS", "valor": 32.00},
            {"id": 4, "data": "2024-05-04", "descricao": "SHELL GAS", "valor": 150.00},
            {"id": 5, "data": "2024-05-05", "descricao": "AMAZON.COM", "valor": 89.90},
        ]
        
        print("Processando transações bancárias...")
        print()
        
        # Extrair descrições
        descricoes = [t['descricao'] for t in transacoes]
        
        # Classificar em lote
        resultado = client.batch_predict(descricoes)
        
        # Combinar resultados com transações originais
        transacoes_classificadas = []
        for transacao in transacoes:
            # Encontrar resultado correspondente
            for res in resultado.get('results', []):
                if res['description'] == transacao['descricao']:
                    transacao['categoria'] = res['category']
                    transacao['confianca'] = res['confidence']
                    transacoes_classificadas.append(transacao)
                    break
        
        # Exibir resultados
        print("Transações Classificadas:")
        print()
        print(f"{'ID':<4} | {'Data':<12} | {'Descrição':<20} | {'Valor':<10} | {'Categoria':<20} | {'Conf.'}")
        print("-" * 95)
        
        for t in transacoes_classificadas:
            print(f"{t['id']:<4} | {t['data']:<12} | {t['descricao'][:18]:<20} | "
                  f"R$ {t['valor']:<7.2f} | {t['categoria'][:18]:<20} | {t['confianca']:.0%}")
        
        print()
        print("✅ Transações classificadas com sucesso!")
        print(f"   Total: {len(transacoes_classificadas)} transações")
        
        # Estatísticas por categoria
        categorias_count = {}
        for t in transacoes_classificadas:
            cat = t['categoria']
            categorias_count[cat] = categorias_count.get(cat, 0) + 1
        
        print()
        print("Distribuição por categoria:")
        for cat, count in categorias_count.items():
            print(f"   - {cat}: {count} transação(ões)")
        
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar à API.")
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        client.close()


def exemplo_tratamento_erros():
    """Exemplo de tratamento de erros"""
    print("=" * 70)
    print("🦆 DuckBill AI - Exemplo de Tratamento de Erros")
    print("=" * 70)
    print()
    
    client = DuckBillClient()
    
    try:
        # Casos de teste com erros esperados
        casos_teste = [
            ("", "Descrição vazia"),
            ("a", "Descrição muito curta"),
            ("x" * 501, "Descrição muito longa"),
            ("Valid description", "Descrição válida")
        ]
        
        print("Testando validações da API:")
        print()
        
        for descricao, caso in casos_teste:
            print(f"Caso: {caso}")
            try:
                result = client.predict(descricao)
                print(f"  ✅ Sucesso: {result.get('category')} ({result.get('confidence'):.2%})")
            except requests.exceptions.HTTPError as e:
                print(f"  ❌ Erro HTTP {e.response.status_code}: {e.response.json().get('error')}")
            except Exception as e:
                print(f"  ❌ Erro: {e}")
            print()
        
    except requests.exceptions.ConnectionError:
        print("❌ Erro: Não foi possível conectar à API.")
    finally:
        client.close()


if __name__ == "__main__":
    import sys
    
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "🦆 DuckBill AI - Exemplos de Uso" + " " * 20 + "║")
    print("║" + " " * 20 + "Sprint 4 - FIAP Challenge" + " " * 23 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    if len(sys.argv) > 1:
        exemplo = sys.argv[1]
        if exemplo == "basico":
            exemplo_uso_basico()
        elif exemplo == "batch":
            exemplo_batch_prediction()
        elif exemplo == "integracao":
            exemplo_integracao_sistema()
        elif exemplo == "erros":
            exemplo_tratamento_erros()
        else:
            print(f"Exemplo '{exemplo}' não encontrado.")
            print("Exemplos disponíveis: basico, batch, integracao, erros")
    else:
        print("Escolha um exemplo:")
        print("  1. Uso Básico")
        print("  2. Predição em Lote")
        print("  3. Integração com Sistema")
        print("  4. Tratamento de Erros")
        print()
        
        escolha = input("Digite o número (1-4) ou 'todos' para executar todos: ").strip()
        print()
        
        if escolha == "1":
            exemplo_uso_basico()
        elif escolha == "2":
            exemplo_batch_prediction()
        elif escolha == "3":
            exemplo_integracao_sistema()
        elif escolha == "4":
            exemplo_tratamento_erros()
        elif escolha.lower() == "todos":
            exemplo_uso_basico()
            print("\n" + "=" * 70 + "\n")
            exemplo_batch_prediction()
            print("\n" + "=" * 70 + "\n")
            exemplo_integracao_sistema()
            print("\n" + "=" * 70 + "\n")
            exemplo_tratamento_erros()
        else:
            print("Opção inválida.")

# Made with Bob
