import unittest
import os
import sys

# Adiciona o diretório atual ao path para importar o sistema_clientes corretamente
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sistema_clientes import SistemaCreditos

class TestSistemaCreditos(unittest.TestCase):
    def setUp(self):
        # Inicializa o sistema com banco em memória para testes isolados
        self.sistema = SistemaCreditos(":memory:")

    def test_cadastro_hospede(self):
        """Testa se o sistema cadastra e recupera um hóspede corretamente."""
        # Usamos um documento tipo RG para simplificar (evita validação matemática de CPF)
        doc = "RG123456"
        nome = "Hospede Teste"
        
        self.sistema.cadastrar_hospede(nome, doc)
        
        recuperado = self.sistema.get_hospede(doc)
        self.assertIsNotNone(recuperado, "O hóspede deveria ter sido encontrado.")
        self.assertEqual(recuperado['nome'], nome.upper(), "O nome deve ser salvo em maiúsculas.")

    def test_fluxo_financeiro(self):
        """Testa o fluxo de adicionar crédito e realizar consumo."""
        doc = "RG999888"
        self.sistema.cadastrar_hospede("Cliente Financeiro", doc)

        # 1. Adicionar Crédito de R$ 100,00
        self.sistema.adicionar_movimentacao(doc, 100.00, "Depósito PIX", "ENTRADA")
        
        saldo, _, _ = self.sistema.get_saldo_info(doc)
        self.assertEqual(saldo, 100.00, "O saldo inicial deveria ser 100.00")

        # 2. Consumir R$ 40,50
        self.sistema.adicionar_movimentacao(doc, 40.50, "Jantar", "SAIDA")
        
        saldo_final, _, _ = self.sistema.get_saldo_info(doc)
        self.assertAlmostEqual(saldo_final, 59.50, places=2, msg="O saldo final está incorreto.")

    def test_validacao_documento_invalido(self):
        """Testa se o sistema rejeita documentos muito curtos."""
        with self.assertRaises(Exception):
            self.sistema.cadastrar_hospede("Erro", "1")

if __name__ == '__main__':
    unittest.main()