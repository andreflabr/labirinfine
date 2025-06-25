import pygame
import operator
import random
import sys
import math
import json
import os
from datetime import datetime

# Cconfiguracao do pygame
pygame.init()
LARGURA, ALTURA = 1280, 760
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Labirinfine - Aventura Matemática")
clock = pygame.time.Clock()

# fontes usadas
fonte_pequena = pygame.font.SysFont('Arial', 18)
fonte_media = pygame.font.SysFont('Arial', 24)
fonte_grande = pygame.font.SysFont('Arial', 36, bold=True)
fonte_titulo = pygame.font.SysFont('Arial', 48, bold=True)

# cores que usei durante o processo, por enquanto nao tem sprites, é tudo cor mesmo
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
VERDE = (0, 255, 0)
VERMELHO = (255, 0, 0)
AZUL = (0, 0, 255)
AMARELO = (255, 255, 0)
CINZA = (128, 128, 128)
CINZA_ESCURO = (50, 50, 50)
ROXO = (128, 0, 128)
LARANJA = (255, 165, 0)
VERDE_CLARO = (144, 238, 144)
AZUL_CLARO = (173, 216, 230)

# aqui é as configurações das fases
class ConfiguracaoFase:
    def __init__(self, numero_fase):
        self.numero = numero_fase
        self.tamanho_labirinto = self._calcular_tamanho_labirinto()
        self.num_inimigos = self._calcular_num_inimigos()
        self.vidas_inimigo = self._calcular_vidas_inimigo()
        self.operacoes_permitidas = self._definir_operacoes()
        self.max_numero = self._calcular_max_numero()
        self.tempo_quiz = self._calcular_tempo_quiz()
        self.vidas_jogador_inicial = self._calcular_vidas_jogador()
        
    # de acordo com o numero da fase o labirinto vai aumentando 
    def _calcular_tamanho_labirinto(self):
        base = 11
        incremento = min(self.numero * 2, 20)
        return base + incremento
    
    # verifica tambem o numero da fase para aumentar quantidade de inimigos
    def _calcular_num_inimigos(self):
        return min(3 + self.numero * 2, 15)
    
    # numero de fases ele calcula as vidas do inimigo, mas acho que nao ta funcionando muito bem ainda, preciso arrumar
    def _calcular_vidas_inimigo(self):
        return 1 + (self.numero - 1) // 3
    
    # e de acordo com a fase vai tendo mais operações matematicas complexas
    def _definir_operacoes(self):
        if self.numero <= 2:
            return ['+', '-']
        elif self.numero <= 4:
            return ['+', '-', 'x']
        elif self.numero <= 6:
            return ['+', '-', 'x', '÷']
        elif self.numero <= 8:
            return ['+', '-', 'x', '÷', '²']
        else:
            return ['+', '-', 'x', '÷', '²', '√']
    

    def _calcular_max_numero(self):
        return min(10 + self.numero * 5, 100)
    
    # esse de tempo é para responder o quiz, coloquei pra quando tiver tempo marcar no inimigo 2 ou 3 se tiver 15s ou 10s respectivamente
    def _calcular_tempo_quiz(self):
        if self.numero <= 3:
            return None
        elif self.numero <= 6:
            return 15
        else:
            return 10
    
    # as vidas é mesma coisa, começa com 5 e de acordo com fase vai mudando
    def _calcular_vidas_jogador(self):
        return 5 + (self.numero - 1) // 4

# aqui é pra salvar o progresso como json mesmo, entao salva bastante informação pras ver em estatisticas depois
class SistemaProgresso:
    def __init__(self):
        self.arquivo_save = "progresso_labirinfine.json"
        self.dados_padrao = {
            "fase_atual": 1,
            "pontuacao_total": 0,
            "melhor_fase": 1,
            "total_inimigos_derrotados": 0,
            "total_perguntas_respondidas": 0,
            "total_acertos": 0,
            "tempo_total_jogado": 0,
            "data_ultimo_jogo": None,
            "configuracoes": {
                "som_ativo": True,
                "dificuldade_personalizada": False
            }
        }
    
    # aqui salva o progresso, mantem o padrão utf8, pra nao dar merda se salvar em latin
    def salvar_progresso(self, jogo):
        try:
            dados = self.carregar_progresso()
            
            dados["fase_atual"] = jogo.fase_atual
            dados["pontuacao_total"] = jogo.pontuacao_total
            dados["melhor_fase"] = max(dados["melhor_fase"], jogo.fase_atual)
            dados["total_inimigos_derrotados"] = jogo.total_inimigos_derrotados
            dados["total_perguntas_respondidas"] = jogo.total_perguntas_respondidas
            dados["total_acertos"] = jogo.total_acertos
            dados["tempo_total_jogado"] = jogo.tempo_total_jogado
            dados["data_ultimo_jogo"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(self.arquivo_save, 'w', encoding='utf-8') as arquivo:
                json.dump(dados, arquivo, indent=4, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Erro ao salvar progresso: {e}")
            return False
    
    # aqui carrega o progresso da mesma forma, pegando o arquivo chamado progresso_labirinfine.json
    def carregar_progresso(self):
        try:
            if os.path.exists(self.arquivo_save):
                with open(self.arquivo_save, 'r', encoding='utf-8') as arquivo:
                    dados = json.load(arquivo)
                    for chave in self.dados_padrao:
                        if chave not in dados:
                            dados[chave] = self.dados_padrao[chave]
                    return dados
            else:
                return self.dados_padrao.copy()
        except Exception as e:
            print(f"Erro ao carregar progresso: {e}")
            return self.dados_padrao.copy()
    
    # pra resetar é mais facil, so verifica se existe o doc e depois exlui ele 
    def resetar_progresso(self):
        try:
            if os.path.exists(self.arquivo_save):
                os.remove(self.arquivo_save)
            return True
        except Exception as e:
            print(f"Erro ao resetar progresso: {e}")
            return False

# o menu tem como usar as setas, o mouse, ou o teclado pra selectionar a opção
class MenuNavegavel:
    def __init__(self, opcoes, titulo="MENU"):
        self.opcoes = opcoes  # lista de dicionários: [{"texto": "...", "acao": funcao}, ...]
        self.titulo = titulo
        self.indice_selecionado = 0
        self.rects_opcoes = []
    
    # pra saber onde o mouse ta passando nas opções
    def atualizar_rects(self):
        self.rects_opcoes = []
        y_inicial = 380
        
        for i, opcao in enumerate(self.opcoes):
            texto = fonte_media.render(opcao["texto"], True, BRANCO)
            rect = pygame.Rect(
                LARGURA//2 - 200, 
                y_inicial + i * 50 - 10, 
                400, 
                40
            )
            self.rects_opcoes.append(rect)
    
    #aqui processa os eventos de mouse e teclado, naquele formato, ou mouse, ou teclado ou as setinhas pra mover 
    def processar_evento(self, event):
        #setinhas
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.indice_selecionado = (self.indice_selecionado - 1) % len(self.opcoes)
            elif event.key == pygame.K_DOWN:
                self.indice_selecionado = (self.indice_selecionado + 1) % len(self.opcoes)
            elif event.key == pygame.K_RETURN:
                return self.opcoes[self.indice_selecionado]["acao"]
        #mouse 
        elif event.type == pygame.MOUSEMOTION:
            pos_mouse = pygame.mouse.get_pos()
            for i, rect in enumerate(self.rects_opcoes):
                if rect.collidepoint(pos_mouse):
                    self.indice_selecionado = i
        #botao do mouse
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Clique esquerdo
                pos_mouse = pygame.mouse.get_pos()
                for i, rect in enumerate(self.rects_opcoes):
                    if rect.collidepoint(pos_mouse):
                        return self.opcoes[i]["acao"]
        
        return None
    
    # desenha a tela preta mesmo
    def desenhar(self, tela, info_progresso=None):
        tela.fill(PRETO)
        
        # titulo
        titulo = fonte_titulo.render(self.titulo, True, AMARELO)
        tela.blit(titulo, (LARGURA//2 - titulo.get_width()//2, 100))
        
        # Informaçoses do progresso se existir é claro
        if info_progresso:
            y_info = 180
            for info in info_progresso:
                texto = fonte_pequena.render(info, True, CINZA)
                tela.blit(texto, (LARGURA//2 - texto.get_width()//2, y_info))
                y_info += 25
        
        # chama para atualiza retangulos das opções
        self.atualizar_rects()
        
        # ddesenha opções
        y_inicial = 380
        for i, opcao in enumerate(self.opcoes):
            cor = VERDE if i == self.indice_selecionado else BRANCO
            cor_fundo = CINZA_ESCURO if i == self.indice_selecionado else None
            
            # Desenha fundo se selecionado
            if cor_fundo:
                pygame.draw.rect(tela, cor_fundo, self.rects_opcoes[i])
                pygame.draw.rect(tela, VERDE, self.rects_opcoes[i], 2)
            
            texto = fonte_media.render(opcao["texto"], True, cor)
            tela.blit(texto, (LARGURA//2 - texto.get_width()//2, y_inicial + i * 50))


# aqui gera o labirinto com um algoritmo de prim meio que modificado lkkkk tive ajuda do chat gpt pra fazer isso funcionar
'''
o uso do algoritmo de prim é pra gerar um labirinto aleatorio com uma rota sem que ele fique em looping dentro do labirinto
sempre vai conectar as partes do labirinto sem deixar caminhos isolados
comeca de uma celula, abre caminhos aleatorios e vai expandindo ate preencher tudo.
'''
def gerar_labirinto(largura, altura):
    lab = [[1 for _ in range(largura)] for _ in range(altura)]
    fronteira = []
    
    x, y = random.randrange(1, largura-1, 2), random.randrange(1, altura-1, 2)
    lab[y][x] = 0
    
    for dx, dy in [(-2,0), (2,0), (0,-2), (0,2)]:
        nx, ny = x+dx, y+dy
        if 0 < nx < largura-1 and 0 < ny < altura-1:
            fronteira.append((nx, ny, x, y))
    
    while fronteira:
        idx = random.randint(0, len(fronteira)-1)
        x, y, px, py = fronteira.pop(idx)
        if lab[y][x] == 1:
            lab[y][x] = 0
            lab[(y+py)//2][(x+px)//2] = 0
            for dx, dy in [(-2,0), (2,0), (0,-2), (0,2)]:
                nx, ny = x+dx, y+dy
                if 0 < nx < largura-1 and 0 < ny < altura-1 and lab[ny][nx] == 1:
                    fronteira.append((nx, ny, x, y))
    
    lab[1][0] = 0
    lab[altura-2][largura-1] = 0
    return lab

# classe que vai gerar a pergunta com base na fase que tiver jogando 
class GeradorQuiz:
    def __init__(self, config_fase):
        self.config = config_fase
        
    def gerar_pergunta(self):
        operacao = random.choice(self.config.operacoes_permitidas)
        
        if operacao == '+':
            return self._gerar_adicao()
        elif operacao == '-':
            return self._gerar_subtracao()
        elif operacao == 'x':
            return self._gerar_multiplicacao()
        elif operacao == '÷':
            return self._gerar_divisao()
        elif operacao == '²':
            return self._gerar_potencia()
        elif operacao == '√':
            return self._gerar_raiz()
    
    # aqui gera automaticamente uma adição com numeros aleatorios mas que nao sao tao grandes pra ficar facil
    def _gerar_adicao(self):
        a = random.randint(1, self.config.max_numero)
        b = random.randint(1, self.config.max_numero)
        resposta = a + b
        pergunta = f"Quanto é {a} + {b}?"
        return pergunta, resposta
    
    # gera subtração da mesma formamque a adição, pra nao ficar dificil 
    def _gerar_subtracao(self):
        a = random.randint(1, self.config.max_numero)
        b = random.randint(1, min(a, self.config.max_numero))
        resposta = a - b
        pergunta = f"Quanto é {a} - {b}?"
        return pergunta, resposta
    
    # gera multiplicação de a e b considerando tbm um numero maximo pra nao ficar dificil
    def _gerar_multiplicacao(self):
        a = random.randint(1, min(12, self.config.max_numero // 5))
        b = random.randint(1, min(12, self.config.max_numero // 5))
        resposta = a * b
        pergunta = f"Quanto é {a} × {b}?"
        return pergunta, resposta
    
    # gera divisao de a e b considerando tbm um numero maximo pra nao ficar dificil
    def _gerar_divisao(self):
        b = random.randint(2, min(10, self.config.max_numero // 5))
        resposta = random.randint(1, self.config.max_numero // b)
        a = b * resposta
        pergunta = f"Quanto é {a} ÷ {b}?"
        return pergunta, resposta
    
    # gera uma potenciação simples tambem pra ser reslvida
    def _gerar_potencia(self):
        base = random.randint(1, min(10, int(math.sqrt(self.config.max_numero))))
        resposta = base ** 2
        pergunta = f"Quanto é {base}²?"
        return pergunta, resposta
    
    #aqui gera uma raiz quadrada, pra isso tbm considera um numero maximo pra nao ficar dificil
    def _gerar_raiz(self):
        resposta = random.randint(1, min(10, int(math.sqrt(self.config.max_numero))))
        numero = resposta ** 2
        pergunta = f"Qual é a √{numero}?"
        return pergunta, resposta
    
    #aqui cria sempre 4 alternativas pro jogador escolher
    def gerar_alternativas(self, resposta_correta):
        alternativas = [resposta_correta]
        
        while len(alternativas) < 4:
            if resposta_correta <= 10:
                erro = resposta_correta + random.randint(-5, 5)
            else:
                erro = resposta_correta + random.randint(-resposta_correta//3, resposta_correta//3)
            
            if erro > 0 and erro != resposta_correta and erro not in alternativas:
                alternativas.append(erro)
        
        random.shuffle(alternativas)
        return alternativas

# classe do jogador que se move no labirinto
class Jogador:
    def __init__(self, labirinto, vidas_iniciais=5):
        self.x, self.y = 0, 1
        self.vidas = vidas_iniciais # inicia com 5 sempre
        self.vidas_maximas = vidas_iniciais
    
    #se move no lairinto 
    def mover(self, dx, dy, labirinto):
        nova_x = self.x + dx
        nova_y = self.y + dy
        
        if (0 <= nova_x < len(labirinto[0]) and 
            0 <= nova_y < len(labirinto) and 
            labirinto[nova_y][nova_x] == 0):
            self.x, self.y = nova_x, nova_y
            return True
        return False
    
    #quando ele perder vidas
    def perder_vida(self):
        self.vidas -= 1
        return self.vidas <= 0
    
    # qando ganhar vidas
    def ganhar_vida(self):
        if self.vidas < self.vidas_maximas:
            self.vidas += 1

# clase do inimigo
'''
pensei o seguinte, quando eu errar o quiz e nao conseguir matar o inimigo, ele é teleportado pra um lugar aleatorio do labirinto, podendo ir pra sua frente de novo ou pra tras
se matar o inimigo aí ele some 100% 

'''
class Inimigo:
    def __init__(self, labirinto, vidas=1):
        self.vidas = vidas
        self.vidas_maximas = vidas
        self.teleportar(labirinto)
    
    # função de teleportar quando errar o quiz 
    def teleportar(self, labirinto):
        tentativas = 0
        while tentativas < 100:
            x = random.randint(1, len(labirinto[0])-2)
            y = random.randint(1, len(labirinto)-2)
            if labirinto[y][x] == 0 and (x != 0 or y != 1):
                self.x, self.y = x, y
                break
            tentativas += 1
    
    #tira a vida do inimigo
    def perder_vida(self):
        self.vidas -= 1
        return self.vidas <= 0

# aqui cria o quiz, tendo qual a resposta correta, as opções, o tempo etc
class InterfaceQuiz:
    def __init__(self, pergunta, alternativas, resposta_correta, tempo_limite=None):
        self.pergunta = pergunta
        self.alternativas = alternativas
        self.resposta_correta = resposta_correta
        self.tempo_limite = tempo_limite
        self.tempo_inicio = pygame.time.get_ticks() if tempo_limite else None
        self.letras = ['A', 'B', 'C', 'D']
        self.indice_selecionado = 0
        self.rects_alternativas = []
    
    # atualiza os retangulos das alternativas se passar o mouse ne
    def atualizar_rects(self):
        self.rects_alternativas = []
        y_inicial = 250
        
        for i in range(len(self.alternativas)):
            rect = pygame.Rect(LARGURA//2 - 200, y_inicial + i*60 - 5, 400, 50)
            self.rects_alternativas.append(rect)
    
    # aqui processa o eveto do mouse ou teclado da navegação no quiz
    def processar_evento(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.indice_selecionado = (self.indice_selecionado - 1) % len(self.alternativas)
            elif event.key == pygame.K_DOWN:
                self.indice_selecionado = (self.indice_selecionado + 1) % len(self.alternativas)
            elif event.key == pygame.K_RETURN:
                return self.letras[self.indice_selecionado]
            elif event.key in [pygame.K_a, pygame.K_b, pygame.K_c, pygame.K_d]:
                return chr(event.key).upper()
        
        if event.type == pygame.MOUSEMOTION:
            pos_mouse = pygame.mouse.get_pos()
            for i, rect in enumerate(self.rects_alternativas):
                if rect.collidepoint(pos_mouse):
                    self.indice_selecionado = i
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Clique esquerdo pra lembrar 
                pos_mouse = pygame.mouse.get_pos()
                for i, rect in enumerate(self.rects_alternativas):
                    if rect.collidepoint(pos_mouse):
                        return self.letras[i]
        
        return None
    
    # aqui desenha a tela 
    def desenhar(self, tela, vidas_jogador):
        tela.fill(CINZA_ESCURO)
        
        # Titulo do quiz
        titulo = fonte_grande.render("DESAFIO MATEMÁTICO", True, AMARELO)
        tela.blit(titulo, (LARGURA//2 - titulo.get_width()//2, 50))
        
        # vidas do jogador
        texto_vidas = fonte_media.render(f"Vidas: {vidas_jogador}", True, VERMELHO)
        tela.blit(texto_vidas, (20, 20))
        
        # tempo se houver
        if self.tempo_limite:
            tempo_restante = self.tempo_limite - (pygame.time.get_ticks() - self.tempo_inicio) // 1000
            if tempo_restante <= 0:
                return True  # Tempo esgotado
            cor_tempo = VERMELHO if tempo_restante <= 5 else BRANCO
            texto_tempo = fonte_media.render(f"Tempo: {tempo_restante}s", True, cor_tempo)
            tela.blit(texto_tempo, (LARGURA - 150, 20))
        
        # Pergunta
        texto_pergunta = fonte_grande.render(self.pergunta, True, BRANCO)
        tela.blit(texto_pergunta, (LARGURA//2 - texto_pergunta.get_width()//2, 150))
        
        # Atualiza os retangulos  das alternativas
        self.atualizar_rects()
        
        # Alternativas
        y_inicial = 250
        for i, alternativa in enumerate(self.alternativas):
            # Determina cores baseado na selecao
            if i == self.indice_selecionado:
                cor_fundo = AZUL_CLARO
                cor_borda = AZUL
                cor_texto = PRETO
            else:
                cor_fundo = (40, 40, 40)
                cor_borda = AZUL
                cor_texto = BRANCO
            
            # Desenha retangulo de fundo
            rect = self.rects_alternativas[i]
            pygame.draw.rect(tela, cor_fundo, rect)
            pygame.draw.rect(tela, cor_borda, rect, 2)
            
            # Texto da alternativa
            texto = fonte_media.render(f"{self.letras[i]}) {alternativa}", True, cor_texto)
            tela.blit(texto, (LARGURA//2 - 180, y_inicial + i*60))
        
        # Instruções para aparecer durante o quiz
        instrucoes = [
            "Use ↑↓ ou mouse para navegar",
            "Pressione ENTER ou clique para responder",
            "Ou use A, B, C, D diretamente"
        ]
        
        y_instrucao = 500
        for instrucao in instrucoes:
            texto = fonte_pequena.render(instrucao, True, CINZA)
            tela.blit(texto, (LARGURA//2 - texto.get_width()//2, y_instrucao))
            y_instrucao += 20
        
        return False  # tempo não esgotado
    
    # aqui verifica a resp
    def verificar_resposta(self, tecla_pressionada):
        if tecla_pressionada in ['A', 'B', 'C', 'D']:
            indice = ord(tecla_pressionada) - ord('A')
            if indice < len(self.alternativas):
                return self.alternativas[indice] == self.resposta_correta
        return False

# classe do jogo
class Jogo:
    def __init__(self):
        self.sistema_progresso = SistemaProgresso()
        self.carregar_progresso()
        self.estado = "MENU"
        self.tempo_inicio_sessao = pygame.time.get_ticks()
        self.menu_principal = None
        self.inicializar_menus()
        self.iniciar_fase()
        
    # inicia os menus de navegaçcao
    def inicializar_menus(self):
        opcoes_menu = [
            {"texto": "Continuar Jogo" if self.fase_atual > 1 else "Novo Jogo", "acao": "continuar"},
            {"texto": "Novo Jogo", "acao": "novo_jogo"},
            {"texto": "Instruções", "acao": "instrucoes"},
            {"texto": "Estatísticas", "acao": "estatisticas"},
            {"texto": "Resetar Progresso", "acao": "resetar"},
            {"texto": "Sair", "acao": "sair"}
        ]
        
        self.menu_principal = MenuNavegavel(opcoes_menu, "LABIRINFINE")
        
    # quando for carregar o progresso salvo no json
    def carregar_progresso(self):
        dados = self.sistema_progresso.carregar_progresso()
        
        self.fase_atual = dados["fase_atual"]
        self.pontuacao_total = dados["pontuacao_total"]
        self.melhor_fase = dados["melhor_fase"]
        self.total_inimigos_derrotados = dados["total_inimigos_derrotados"]
        self.total_perguntas_respondidas = dados["total_perguntas_respondidas"]
        self.total_acertos = dados["total_acertos"]
        self.tempo_total_jogado = dados["tempo_total_jogado"]
        
        self.pontuacao_sessao = 0
        
    # pra salvar o progresso no json
    def salvar_progresso(self):
        tempo_sessao = (pygame.time.get_ticks() - self.tempo_inicio_sessao) // 1000
        self.tempo_total_jogado += tempo_sessao
        self.tempo_inicio_sessao = pygame.time.get_ticks()
        
        return self.sistema_progresso.salvar_progresso(self)
    
    # exclui o json pra resetar o progresso 
    def resetar_progresso(self):
        if self.sistema_progresso.resetar_progresso():
            self.carregar_progresso()
            self.iniciar_fase()
            return True
        return False
    
    # as configurações da fase, tamanho de labirinto, inimigo, fase atual etc e tal
    def iniciar_fase(self):
        self.config_fase = ConfiguracaoFase(self.fase_atual)
        tamanho = self.config_fase.tamanho_labirinto
        
        if tamanho % 2 == 0:
            tamanho += 1
            
        self.labirinto = gerar_labirinto(tamanho, tamanho)
        self.tamanho_celula = min(LARGURA // tamanho, (ALTURA - 100) // tamanho)
        
        self.jogador = Jogador(self.labirinto, self.config_fase.vidas_jogador_inicial)
        self.inimigos = [Inimigo(self.labirinto, self.config_fase.vidas_inimigo) 
                        for _ in range(self.config_fase.num_inimigos)]
        
        self.gerador_quiz = GeradorQuiz(self.config_fase)
        self.interface_quiz = None
        self.inimigo_ativo = None
    
    # avança de fase, ai muda fase atual pra gerar labirinto novo, mudar inimigo e toda estrutura de geração da fase nova
    def avancar_fase(self):
        self.fase_atual += 1
        bonus_fase = 100 * self.fase_atual
        self.pontuacao_total += bonus_fase
        self.pontuacao_sessao += bonus_fase
        self.salvar_progresso()
        self.iniciar_fase()
    
    # verifica as colisoes com os inimigos 
    def verificar_colisao(self):
        for inimigo in self.inimigos:
            if self.jogador.x == inimigo.x and self.jogador.y == inimigo.y:
                return inimigo
        return None
    
    # inicia o quiz, gera a pergunta e alternativas e cria a interface do quiz
    def iniciar_quiz(self, inimigo):
        pergunta, resposta = self.gerador_quiz.gerar_pergunta()
        alternativas = self.gerador_quiz.gerar_alternativas(resposta)
        self.interface_quiz = InterfaceQuiz(
            pergunta, alternativas, resposta, 
            self.config_fase.tempo_quiz
        )
        self.inimigo_ativo = inimigo
        self.estado = "QUIZ"
    
    # aqui processa a resposta que o jogador deu
    def processar_resposta_quiz(self, resposta_correta):
        self.total_perguntas_respondidas += 1
        
        if resposta_correta:
            self.total_acertos += 1
            if self.inimigo_ativo.perder_vida():
                self.inimigos.remove(self.inimigo_ativo)
                self.total_inimigos_derrotados += 1
                pontos = 10
                self.pontuacao_total += pontos
                self.pontuacao_sessao += pontos
                
                if len(self.inimigos) < 3:
                    self.inimigos.append(Inimigo(self.labirinto, self.config_fase.vidas_inimigo))
            else:
                self.inimigo_ativo.teleportar(self.labirinto)
                pontos = 5
                self.pontuacao_total += pontos
                self.pontuacao_sessao += pontos
        else:
            if self.jogador.perder_vida():
                self.salvar_progresso()
                self.estado = "GAME_OVER"
                return
            self.inimigo_ativo.teleportar(self.labirinto)
        
        self.interface_quiz = None
        self.inimigo_ativo = None
        self.estado = "JOGANDO"
    
    def verificar_vitoria(self):
        tamanho = len(self.labirinto)
        return (self.jogador.x == tamanho - 1 and 
                self.jogador.y == tamanho - 2)
      
    def desenhar_jogo(self, tela):
        tela.fill(PRETO)
        
        # Informações do jogo
        info_y = 10
        texto_fase = fonte_media.render(f"Fase: {self.fase_atual}", True, AMARELO)
        texto_vidas = fonte_media.render(f"Vidas: {self.jogador.vidas}", True, VERMELHO)
        texto_pontos = fonte_media.render(f"Pontos: {self.pontuacao_total}", True, BRANCO)
        texto_inimigos = fonte_media.render(f"Inimigos: {len(self.inimigos)}", True, ROXO)
        
        tela.blit(texto_fase, (10, info_y))
        tela.blit(texto_vidas, (150, info_y))
        tela.blit(texto_pontos, (300, info_y))
        tela.blit(texto_inimigos, (500, info_y))
        
        # Offset para sempre centralizar o labirinto
        offset_x = (LARGURA - len(self.labirinto[0]) * self.tamanho_celula) // 2
        offset_y = 50
        
        # Desenhar labirinto
        for y, linha in enumerate(self.labirinto):
            for x, celula in enumerate(linha):
                rect = pygame.Rect(
                    offset_x + x * self.tamanho_celula,
                    offset_y + y * self.tamanho_celula,
                    self.tamanho_celula,
                    self.tamanho_celula
                )
                
                if celula == 1:
                    pygame.draw.rect(tela, CINZA_ESCURO, rect)
                else:
                    pygame.draw.rect(tela, BRANCO, rect)
        
        # Desenhar saída
        saida_x = len(self.labirinto[0]) - 1
        saida_y = len(self.labirinto) - 2
        rect_saida = pygame.Rect(
            offset_x + saida_x * self.tamanho_celula,
            offset_y + saida_y * self.tamanho_celula,
            self.tamanho_celula,
            self.tamanho_celula
        )
        pygame.draw.rect(tela, VERDE, rect_saida)
        
        # Desenhar inimigos
        for inimigo in self.inimigos:
            rect_inimigo = pygame.Rect(
                offset_x + inimigo.x * self.tamanho_celula + 2,
                offset_y + inimigo.y * self.tamanho_celula + 2,
                self.tamanho_celula - 4,
                self.tamanho_celula - 4
            )
            pygame.draw.rect(tela, VERMELHO, rect_inimigo)
            
            if inimigo.vidas > 1:
                texto_vida = fonte_pequena.render(str(inimigo.vidas), True, BRANCO)
                tela.blit(texto_vida, (rect_inimigo.centerx - 5, rect_inimigo.centery - 8))
        
        # Desenhar jogador
        rect_jogador = pygame.Rect(
            offset_x + self.jogador.x * self.tamanho_celula + 2,
            offset_y + self.jogador.y * self.tamanho_celula + 2,
            self.tamanho_celula - 4,
            self.tamanho_celula - 4
        )
        pygame.draw.rect(tela, AZUL, rect_jogador)
        
        # Instruções pra ficar no rodapé do jogo
        instrucoes = [
            "P - Pausar | S - Salvar | ESC - Menu Principal"
        ]
        
        for i, instrucao in enumerate(instrucoes):
            texto = fonte_pequena.render(instrucao, True, CINZA)
            tela.blit(texto, (10, ALTURA - 80 + i * 15))

# a opção de instruções eu criei pra ficar bacana, foi simples colocar 
def desenhar_instrucoes(tela):
    tela.fill(PRETO)
    
    titulo = fonte_grande.render("INSTRUÇÕES", True, AMARELO)
    tela.blit(titulo, (LARGURA//2 - titulo.get_width()//2, 50))
    
    instrucoes = [
        "OBJETIVO:",
        "  - Navegue pelo labirinto até a área verde",
        "  - Resolva problemas matemáticos para derrotar inimigos",
        "  - Avance pelas fases que ficam progressivamente mais difíceis",
        "",
        "CONTROLES:",
        "  - Setas do teclado: Mover o jogador",
        "  - Mouse ou ↑↓: Navegar nos menus",
        "  - ENTER ou clique: Selecionar opção",
        "  - A, B, C, D: Responder quiz diretamente",
        "  - P: Pausar jogo",
        "  - S: Salvar progresso manualmente",
        "  - ESC: Menu principal",
        "",
        "SISTEMA DE SAVE:",
        "  - O progresso é salvo automaticamente ao avançar de fase",
        "  - Pressione S para salvar manualmente",
        "  - O jogo salva automaticamente ao sair",
        "",
        "Pressione ESC para voltar"
    ]
    
    y = 120
    for linha in instrucoes:
        if linha.startswith("OBJETIVO") or linha.startswith("CONTROLES") or linha.startswith("SISTEMA"):
            texto = fonte_media.render(linha, True, AMARELO)
        elif linha.startswith("  •"):
            texto = fonte_pequena.render(linha, True, BRANCO)
        else:
            texto = fonte_pequena.render(linha, True, CINZA)
        
        tela.blit(texto, (50, y))
        y += 25

# a tela de estatistica pra mostrar as infos 
def desenhar_estatisticas(tela, jogo):
    tela.fill(PRETO)
    
    titulo = fonte_grande.render("ESTATÍSTICAS", True, AMARELO)
    tela.blit(titulo, (LARGURA//2 - titulo.get_width()//2, 50))
    
    tempo_formatado = f"{jogo.tempo_total_jogado // 3600:02d}:{(jogo.tempo_total_jogado % 3600) // 60:02d}:{jogo.tempo_total_jogado % 60:02d}"
    taxa_acerto = (jogo.total_acertos / max(1, jogo.total_perguntas_respondidas)) * 100
    
    estatisticas = [
        f"Fase Atual: {jogo.fase_atual}",
        f"Melhor Fase Alcançada: {jogo.melhor_fase}",
        f"Pontuação Total: {jogo.pontuacao_total:,}",
        f"Inimigos Derrotados: {jogo.total_inimigos_derrotados:,}",
        f"Perguntas Respondidas: {jogo.total_perguntas_respondidas:,}",
        f"Respostas Corretas: {jogo.total_acertos:,}",
        f"Taxa de Acerto: {taxa_acerto:.1f}%",
        f"Tempo Total Jogado: {tempo_formatado}",
        "",
        "Pressione ESC para voltar"
    ]
    
    y = 120
    for stat in estatisticas:
        if stat == "":
            y += 20
            continue
        
        if "Pressione" in stat:
            cor = CINZA
        elif any(palavra in stat for palavra in ["Fase", "Melhor", "Pontuação"]):
            cor = AMARELO
        else:
            cor = BRANCO
            
        texto = fonte_media.render(stat, True, cor)
        tela.blit(texto, (LARGURA//2 - texto.get_width()//2, y))
        y += 35

# coloquei pausa com o teclado se apertar P de Pause
def desenhar_pausa(tela):
    overlay = pygame.Surface((LARGURA, ALTURA))
    overlay.set_alpha(128)
    overlay.fill(PRETO)
    tela.blit(overlay, (0, 0))
    
    texto_pausa = fonte_titulo.render("PAUSADO", True, AMARELO)
    texto_continuar = fonte_media.render("Pressione P para continuar", True, BRANCO)
    texto_sair = fonte_media.render("ESC para menu principal", True, BRANCO)
    
    tela.blit(texto_pausa, (LARGURA//2 - texto_pausa.get_width()//2, ALTURA//2 - 80))
    tela.blit(texto_continuar, (LARGURA//2 - texto_continuar.get_width()//2, ALTURA//2 - 20))
    tela.blit(texto_sair, (LARGURA//2 - texto_sair.get_width()//2, ALTURA//2 + 60))

# desenha na tela que a fase foi concluida e que ta preparando a fase nova e salva o progresso tbm 
def desenhar_vitoria_fase(tela, fase):
    tela.fill(PRETO)
    
    titulo = fonte_titulo.render("FASE CONCLUÍDA!", True, VERDE)
    proxima = fonte_grande.render(f"Preparando Fase {fase + 1}...", True, BRANCO)
    salvo = fonte_media.render("Progresso salvo automaticamente!", True, AMARELO)
    
    tela.blit(titulo, (LARGURA//2 - titulo.get_width()//2, ALTURA//2 - 80))
    tela.blit(proxima, (LARGURA//2 - proxima.get_width()//2, ALTURA//2 - 20))
    tela.blit(salvo, (LARGURA//2 - salvo.get_width()//2, ALTURA//2 + 40))

# se acabar as vidas e morrer desenha o game over na tela e ate oned chegou
def desenhar_game_over(tela, fase, pontuacao):
    tela.fill(PRETO)
    
    titulo = fonte_titulo.render("GAME OVER", True, VERMELHO)
    fase_texto = fonte_grande.render(f"Você chegou até a Fase {fase}", True, BRANCO)
    pontos_texto = fonte_grande.render(f"Pontuação Final: {pontuacao}", True, AMARELO)
    salvo = fonte_media.render("Progresso salvo!", True, VERDE)
    reiniciar = fonte_media.render("Pressione R para jogar novamente", True, BRANCO)
    menu = fonte_media.render("ESC para voltar ao menu", True, BRANCO)
    
    tela.blit(titulo, (LARGURA//2 - titulo.get_width()//2, ALTURA//2 - 140))
    tela.blit(fase_texto, (LARGURA//2 - fase_texto.get_width()//2, ALTURA//2 - 80))
    tela.blit(pontos_texto, (LARGURA//2 - pontos_texto.get_width()//2, ALTURA//2 - 40))
    tela.blit(salvo, (LARGURA//2 - salvo.get_width()//2, ALTURA//2))
    tela.blit(reiniciar, (LARGURA//2 - reiniciar.get_width()//2, ALTURA//2 + 60))
    tela.blit(menu, (LARGURA//2 - menu.get_width()//2, ALTURA//2 + 100))

# só pra mostrar que foi salvo o progresso quando termina a fase 
def mostrar_mensagem_save(tela, sucesso=True):
    overlay = pygame.Surface((400, 100))
    overlay.set_alpha(200)
    overlay.fill(VERDE if sucesso else VERMELHO)
    
    x = (LARGURA - 400) // 2
    y = 100
    
    tela.blit(overlay, (x, y))
    
    mensagem = "Progresso salvo com sucesso!" if sucesso else "Erro ao salvar progresso!"
    texto = fonte_media.render(mensagem, True, BRANCO)
    tela.blit(texto, (x + 200 - texto.get_width()//2, y + 40))

# Loop principal do jogo
def main():
    jogo = Jogo()
    TEMPO_ENTRE_MOVIMENTOS = 150
    ultimo_movimento = 0
    mensagem_save_tempo = 0
    mensagem_save_sucesso = True
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                jogo.salvar_progresso()
                pygame.quit()
                sys.exit()
            
            # Menu principal
            if jogo.estado == "MENU":
                acao = jogo.menu_principal.processar_evento(event)
                if acao:
                    if acao == "continuar":
                        jogo.estado = "JOGANDO"
                    elif acao == "novo_jogo":
                        jogo.resetar_progresso()
                        jogo = Jogo()
                        jogo.estado = "JOGANDO"
                    elif acao == "instrucoes":
                        jogo.estado = "INSTRUCOES"
                    elif acao == "estatisticas":
                        jogo.estado = "ESTATISTICAS"
                    elif acao == "resetar":
                        if jogo.resetar_progresso():
                            jogo = Jogo()
                    elif acao == "sair":
                        jogo.salvar_progresso()
                        pygame.quit()
                        sys.exit()
           
            #Instruções e estatíisticas
            elif jogo.estado in ["INSTRUCOES", "ESTATISTICAS"]:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        jogo.estado = "MENU"
            
            #pausa
            elif jogo.estado == "PAUSADO":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        jogo.estado = "JOGANDO"
                    elif event.key == pygame.K_s:
                        sucesso = jogo.salvar_progresso()
                        mensagem_save_tempo = pygame.time.get_ticks() + 2000
                        mensagem_save_sucesso = sucesso
                    elif event.key == pygame.K_ESCAPE:
                        jogo.salvar_progresso()
                        jogo.estado = "MENU"
            
            # gameover
            elif jogo.estado == "GAME_OVER":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        jogo.resetar_progresso()
                        jogo = Jogo()
                        jogo.estado = "JOGANDO"
                    elif event.key == pygame.K_ESCAPE:
                        jogo.estado = "MENU"
            
            # Jogo normal
            elif jogo.estado == "JOGANDO":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        jogo.estado = "PAUSADO"
                    elif event.key == pygame.K_s:
                        sucesso = jogo.salvar_progresso()
                        mensagem_save_tempo = pygame.time.get_ticks() + 2000
                        mensagem_save_sucesso = sucesso
                    elif event.key == pygame.K_ESCAPE:
                        jogo.salvar_progresso()
                        jogo.estado = "MENU"
            
            # Quiz com navegação por mouse e teclado
            elif jogo.estado == "QUIZ":
                resposta = jogo.interface_quiz.processar_evento(event)
                if resposta:
                    resposta_correta = jogo.interface_quiz.verificar_resposta(resposta)
                    jogo.processar_resposta_quiz(resposta_correta)
        
        # logica do jogo
        if jogo.estado == "JOGANDO":
            agora = pygame.time.get_ticks()
            if agora - ultimo_movimento > TEMPO_ENTRE_MOVIMENTOS:
                keys = pygame.key.get_pressed()
                moveu = False
                
                if keys[pygame.K_LEFT]:
                    moveu = jogo.jogador.mover(-1, 0, jogo.labirinto)
                elif keys[pygame.K_RIGHT]:
                    moveu = jogo.jogador.mover(1, 0, jogo.labirinto)
                elif keys[pygame.K_UP]:
                    moveu = jogo.jogador.mover(0, -1, jogo.labirinto)
                elif keys[pygame.K_DOWN]:
                    moveu = jogo.jogador.mover(0, 1, jogo.labirinto)
                
                if moveu:
                    ultimo_movimento = agora
            
            inimigo_colidido = jogo.verificar_colisao()
            if inimigo_colidido:
                jogo.iniciar_quiz(inimigo_colidido)
            
            if jogo.verificar_vitoria():
                jogo.estado = "VITORIA_FASE"
        
        elif jogo.estado == "QUIZ":
            if jogo.interface_quiz and jogo.interface_quiz.tempo_limite:
                tempo_decorrido = (pygame.time.get_ticks() - jogo.interface_quiz.tempo_inicio) // 1000
                if tempo_decorrido >= jogo.interface_quiz.tempo_limite:
                    jogo.processar_resposta_quiz(False)
        
        elif jogo.estado == "VITORIA_FASE":
            pygame.time.wait(2000)
            jogo.avancar_fase()
            jogo.estado = "JOGANDO"
        
        # Renderizaçao
        if jogo.estado == "MENU":
            jogo.menu_principal.desenhar(tela)
        elif jogo.estado == "INSTRUCOES":
            desenhar_instrucoes(tela)
        elif jogo.estado == "ESTATISTICAS":
            desenhar_estatisticas(tela, jogo)
        elif jogo.estado == "JOGANDO":
            jogo.desenhar_jogo(tela)
        elif jogo.estado == "PAUSADO":
            jogo.desenhar_jogo(tela)
            desenhar_pausa(tela)
        elif jogo.estado == "QUIZ":
            timeout = jogo.interface_quiz.desenhar(tela, jogo.jogador.vidas)
            if timeout:
                jogo.processar_resposta_quiz(False)
        elif jogo.estado == "VITORIA_FASE":
            desenhar_vitoria_fase(tela, jogo.fase_atual)
        elif jogo.estado == "GAME_OVER":
            desenhar_game_over(tela, jogo.fase_atual, jogo.pontuacao_total)
        
        # Mostrar mensagem de save se necessário
        if mensagem_save_tempo > pygame.time.get_ticks():
            mostrar_mensagem_save(tela, mensagem_save_sucesso)
        
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
