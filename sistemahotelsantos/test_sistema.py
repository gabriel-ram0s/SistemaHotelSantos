import unittest
import os
import sys
from datetime import datetime

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

    def test_fluxo_multas(self):
        """Testa o fluxo de adicionar multa, pagar parcialmente e verificar dívida."""
        doc = "RG_MULTA"
        self.sistema.cadastrar_hospede("Cliente Multado", doc)

        # 1. Adicionar multa de R$ 150.00
        self.sistema.adicionar_multa(doc, 150.00, "Danos ao quarto")
        divida = self.sistema.get_divida_multas(doc)
        self.assertEqual(divida, 150.00, "A dívida inicial de multa está incorreta.")

        # 2. Pagar R$ 50.00 da multa
        self.sistema.pagar_multa(doc, 50.00, "Dinheiro")
        divida_restante = self.sistema.get_divida_multas(doc)
        self.assertAlmostEqual(divida_restante, 100.00, places=2, msg="A dívida restante após pagamento parcial está incorreta.")

        # 3. Tentar pagar mais do que a dívida
        with self.assertRaises(Exception, msg="Deveria impedir pagamento maior que a dívida"):
            self.sistema.pagar_multa(doc, 100.01, "PIX")

    def test_validacao_documento_invalido(self):
        """Testa se o sistema rejeita documentos muito curtos."""
        with self.assertRaises(Exception):
            self.sistema.cadastrar_hospede("Erro", "1")

    def test_exportacao_financeira(self):
        """Testa se a exportação do histórico financeiro gera um arquivo."""
        # Popula com dados
        doc = "RG_EXPORT"
        self.sistema.cadastrar_hospede("Cliente Exportacao", doc)
        self.sistema.adicionar_movimentacao(doc, 50.00, "Teste", "ENTRADA")
        
        # Teste 1: Exportação Completa
        arquivo = self.sistema.exportar_historico_financeiro_csv()
        self.assertTrue(os.path.exists(arquivo), "O arquivo CSV não foi criado.")
        if os.path.exists(arquivo): os.remove(arquivo)

        # Teste 2: Exportação Filtrada (Mês Atual)
        mes_atual = datetime.now().strftime("%m/%Y")
        arquivo_filt = self.sistema.exportar_historico_financeiro_csv(mes_ano=mes_atual)
        self.assertTrue(os.path.exists(arquivo_filt), "O arquivo CSV filtrado não foi criado.")
        if os.path.exists(arquivo_filt): os.remove(arquivo_filt)

    def test_comparacao_versao(self):
        """Testa a lógica de comparação de versões semânticas."""
        # Caso onde string simples falharia ("4.10" < "4.9" é False alfabeticamente, mas True semanticamente)
        v_atual = "4.9.0"
        v_nova = "4.10.0"
        
        t_atual = self.sistema._parse_version(v_atual)
        t_nova = self.sistema._parse_version(v_nova)
        
        self.assertTrue(t_nova > t_atual, f"Erro na comparação de versão: {v_nova} deveria ser maior que {v_atual}")

    def test_relatorio_fechamento(self):
        """Testa a geração do PDF de fechamento de caixa."""
        doc = "DOC_FECHAMENTO"
        self.sistema.cadastrar_hospede("Cliente Fechamento", doc)
        self.sistema.adicionar_movimentacao(doc, 100.00, "Teste", "ENTRADA")
        
        hoje = datetime.now().strftime("%Y-%m-%d")
        arquivo = self.sistema.gerar_pdf_fechamento(hoje)
        self.assertTrue(os.path.exists(arquivo), "PDF de fechamento não criado.")
        if os.path.exists(arquivo): os.remove(arquivo)

if __name__ == '__main__':
    unittest.main()