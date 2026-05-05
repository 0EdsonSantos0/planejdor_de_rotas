from flask import Flask, render_template, request, jsonify
import math, heapq
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
import folium

app = Flask(__name__)

COORDENADAS_ESTADOS = {
    'AC': (-9.9747, -67.8076),
    'AL': (-9.6659, -35.7350),
    'AP': (0.0349, -51.0694),
    'AM': (-3.1186, -60.0212),
    'BA': (-12.9718, -38.5011),
    'CE': (-3.7166, -38.5423),
    'DF': (-15.7795, -47.9297),
    'ES': (-20.3155, -40.3128),
    'GO': (-16.6864, -49.2643),
    'MA': (-2.5387, -44.2825),
    'MT': (-15.6010, -56.0974),
    'MS': (-20.4486, -54.6295),
    'MG': (-19.9208, -43.9378),
    'PA': (-1.4554, -48.4907),
    'PB': (-7.1150, -34.8641),
    'PR': (-25.4284, -49.2733),
    'PE': (-8.0540, -34.8813),
    'PI': (-5.0919, -42.8034),
    'RJ': (-22.9068, -43.1729),
    'RN': (-5.7935, -35.1996),
    'RS': (-30.0346, -51.2177),
    'RO': (-8.7619, -63.9039),
    'RR': (2.8238, -60.6753),
    'SC': (-27.5954, -48.5480),
    'SP': (-23.5505, -46.6333),
    'SE': (-10.9167, -37.0500),
    'TO': (-10.2128, -48.3603)
};

def calcular_distancia_haversine(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@dataclass(frozen=True)
class Pedido:
    id: str
    destino: str
    volume: int
    janela_tempo_max: float

@dataclass
class Veiculo:
    modelo: str
    capacidade_maxima: int  
    velocidade_media: float
    local_atual: str

class GrafoTransito:
    def __init__(self):
        self.conexoes = {no: {} for no in COORDENADAS_ESTADOS}

    def adicionar_rodovia(self, origem, destino, fator_transito=1.0):
        distancia = calcular_distancia_haversine(COORDENADAS_ESTADOS[origem], COORDENADAS_ESTADOS[destino])
        self.conexoes[origem][destino] = (distancia, fator_transito)
        self.conexoes[destino][origem] = (distancia, fator_transito)

    def calcular_tempo_real(self, origem, destino, velocidade):
        distancia, fator = self.conexoes[origem][destino]
        return (distancia / velocidade) * fator

    def atualizar_transito(self, origem, destino, novo_fator):
        if destino in self.conexoes.get(origem, {}):
            tempo_base = self.conexoes[origem][destino][0]
            self.conexoes[origem][destino] = (tempo_base, novo_fator)
            self.conexoes[destino][origem] = (tempo_base, novo_fator)

@dataclass(order=True)
class EstadoBusca:
    custo_f: float
    custo_g: float
    local_atual: str = field(compare=False)
    capacidade_restante: int = field(compare=False)
    pedidos_pendentes: frozenset = field(compare=False)
    caminho: List[str] = field(compare=False)

    def is_objetivo(self): return len(self.pedidos_pendentes) == 0

def heuristica_geografica(estado, velocidade_veiculo):
    if not estado.pedidos_pendentes: return 0.0
    coord_atual = COORDENADAS_ESTADOS[estado.local_atual]
    max_tempo = max([calcular_distancia_haversine(coord_atual, COORDENADAS_ESTADOS[p.destino]) / velocidade_veiculo for p in estado.pedidos_pendentes])
    return max_tempo

def planejar_rota_a_star(origem, veiculo: Veiculo, pedidos, mapa):
    estado_inicial = EstadoBusca(0, 0, origem, veiculo.capacidade_maxima, frozenset(pedidos), [origem])
    fronteira = []
    heapq.heappush(fronteira, estado_inicial)
    visitados = {}

    while fronteira:
        estado_atual = heapq.heappop(fronteira)
        if estado_atual.is_objetivo(): return estado_atual.caminho, estado_atual.custo_g

        chave = (estado_atual.local_atual, estado_atual.pedidos_pendentes)
        if chave in visitados and visitados[chave] <= estado_atual.custo_g: continue
        visitados[chave] = estado_atual.custo_g

        for vizinho in mapa.conexoes[estado_atual.local_atual]:
            tempo_viagem = mapa.calcular_tempo_real(estado_atual.local_atual, vizinho, veiculo.velocidade_media)
            novo_tempo = estado_atual.custo_g + tempo_viagem
            novos_pedidos = set(estado_atual.pedidos_pendentes)
            nova_capacidade = estado_atual.capacidade_restante

            pedido_entregue = next((p for p in novos_pedidos if p.destino == vizinho), None)
            if pedido_entregue:
                if novo_tempo > pedido_entregue.janela_tempo_max: continue
                if pedido_entregue.volume > nova_capacidade: continue
                novos_pedidos.remove(pedido_entregue)
                nova_capacidade += pedido_entregue.volume # Libera espaço

            novo_estado = EstadoBusca(0, novo_tempo, vizinho, nova_capacidade, frozenset(novos_pedidos), estado_atual.caminho + [vizinho])
            novo_estado.custo_f = novo_estado.custo_g + heuristica_geografica(novo_estado, veiculo.velocidade_media)
            heapq.heappush(fronteira, novo_estado)

    return None, float('inf')

def gerar_mapa_html(mapa_transito, rota_destaque=None, trajeto_feito=None):
    mapa_web = folium.Map(location=[-15.78, -47.93], zoom_start=4, tiles='cartodbpositron')
    for estado, coord in COORDENADAS_ESTADOS.items():
        folium.CircleMarker(location=coord, radius=3, color="gray", fill=True, opacity=0.3).add_to(mapa_web)
    if trajeto_feito and len(trajeto_feito) > 1:
        pontos_rastro = [COORDENADAS_ESTADOS[loc] for loc in trajeto_feito]
        folium.PolyLine(pontos_rastro, color="#7F8C8D", weight=3, opacity=0.6, dash_array='5, 10').add_to(mapa_web)
    if rota_destaque and len(rota_destaque) > 1:
        pontos_rota = [COORDENADAS_ESTADOS[loc] for loc in rota_destaque]
        folium.PolyLine(pontos_rota, color="#E74C3C", weight=5, opacity=0.8).add_to(mapa_web)
        folium.Marker(location=pontos_rota[-1], icon=folium.Icon(color='darkred', icon='flag')).add_to(mapa_web)
    
    pos = COORDENADAS_ESTADOS[rota_destaque[0]] if rota_destaque else (COORDENADAS_ESTADOS[trajeto_feito[-1]] if trajeto_feito else None)
    if pos: folium.Marker(location=pos, icon=folium.Icon(color='red', icon='truck', prefix='fa')).add_to(mapa_web)
    
    # Renderiza o mapa para HTML puro para enviar ao frontend
    return mapa_web.get_root().render()

mapa_br = GrafoTransito()

# REGIÃO SUL
mapa_br.adicionar_rodovia('RS', 'SC')
mapa_br.adicionar_rodovia('SC', 'PR')

# REGIÃO SUDESTE
mapa_br.adicionar_rodovia('PR', 'SP')
mapa_br.adicionar_rodovia('SP', 'RJ')
mapa_br.adicionar_rodovia('SP', 'MG')
mapa_br.adicionar_rodovia('SP', 'MS')
mapa_br.adicionar_rodovia('RJ', 'MG')
mapa_br.adicionar_rodovia('RJ', 'ES')
mapa_br.adicionar_rodovia('MG', 'ES')
mapa_br.adicionar_rodovia('MG', 'GO')
mapa_br.adicionar_rodovia('MG', 'BA')
mapa_br.adicionar_rodovia('ES', 'BA')

# REGIÃO CENTRO-OESTE
mapa_br.adicionar_rodovia('MS', 'MT')
mapa_br.adicionar_rodovia('MS', 'GO')
mapa_br.adicionar_rodovia('MT', 'GO')
mapa_br.adicionar_rodovia('MT', 'RO') 
mapa_br.adicionar_rodovia('MT', 'PA') 
mapa_br.adicionar_rodovia('MT', 'AM') 
mapa_br.adicionar_rodovia('GO', 'DF')
mapa_br.adicionar_rodovia('GO', 'TO') 
mapa_br.adicionar_rodovia('GO', 'BA') 

# REGIÃO NORDESTE
mapa_br.adicionar_rodovia('BA', 'SE')
mapa_br.adicionar_rodovia('BA', 'AL')
mapa_br.adicionar_rodovia('BA', 'PE')
mapa_br.adicionar_rodovia('BA', 'PI')
mapa_br.adicionar_rodovia('SE', 'AL')
mapa_br.adicionar_rodovia('AL', 'PE')
mapa_br.adicionar_rodovia('PE', 'PB')
mapa_br.adicionar_rodovia('PE', 'CE')
mapa_br.adicionar_rodovia('PE', 'PI')
mapa_br.adicionar_rodovia('PB', 'RN')
mapa_br.adicionar_rodovia('PB', 'CE')
mapa_br.adicionar_rodovia('RN', 'CE')
mapa_br.adicionar_rodovia('CE', 'PI')
mapa_br.adicionar_rodovia('PI', 'MA')
mapa_br.adicionar_rodovia('PI', 'TO') 
mapa_br.adicionar_rodovia('MA', 'PA') 
mapa_br.adicionar_rodovia('MA', 'TO') 

# REGIÃO NORTE
mapa_br.adicionar_rodovia('TO', 'PA')
mapa_br.adicionar_rodovia('PA', 'AP')
mapa_br.adicionar_rodovia('PA', 'RR')
mapa_br.adicionar_rodovia('PA', 'AM')
mapa_br.adicionar_rodovia('AM', 'RR')
mapa_br.adicionar_rodovia('AM', 'AC')
mapa_br.adicionar_rodovia('AM', 'RO')
mapa_br.adicionar_rodovia('RO', 'AC')

simulacao_estado = {
    "ativo": False, "veiculo": None, "pedidos": [], "local_atual": "",
    "trajeto": [], "tempo_acumulado": 0.0, "rota_atual": []
}   

# API
@app.route('/')
def index():
    return render_template('index.html', estados=list(COORDENADAS_ESTADOS.keys()))

@app.route('/api/iniciar', methods=['POST'])
def iniciar_simulacao():
    dados = request.json
    simulacao_estado['local_atual'] = dados['origem']
    simulacao_estado['trajeto'] = [dados['origem']]
    simulacao_estado['tempo_acumulado'] = 0.0
    simulacao_estado['distancia_acumulada'] = 0.0 # NOVO: Guarda a distância total
    simulacao_estado['veiculo'] = Veiculo(dados['veiculo'], int(dados['capacidade']), float(dados['velocidade']), dados['origem'])
    simulacao_estado['pedidos'] = [Pedido(p['id'], p['destino'], int(p['volume']), float(p['janela'])) for p in dados['pedidos']]
    simulacao_estado['ativo'] = True
    
    return avancar_passo(simular_apenas=True)

@app.route('/api/avancar', methods=['POST'])
def avancar():
    return avancar_passo(simular_apenas=False)

def avancar_passo(simular_apenas=False):
    # Se a simulação já acabou, retorna o resumo
    if not simulacao_estado['ativo'] or not simulacao_estado['pedidos']:
        return jsonify({
            "status": "concluido", 
            "html_mapa": gerar_mapa_html(mapa_br, trajeto_feito=simulacao_estado['trajeto']),
            "trajeto_total": " -> ".join(simulacao_estado['trajeto']),
            "tempo_total": round(simulacao_estado['tempo_acumulado'], 2),
            "distancia_total": round(simulacao_estado['distancia_acumulada'], 2)
        })

    # 1. Se não for só simulação (for um passo real), movemos o caminhão PRIMEIRO
    if not simular_apenas:
        rota_temp, _ = planejar_rota_a_star(simulacao_estado['local_atual'], simulacao_estado['veiculo'], simulacao_estado['pedidos'], mapa_br)
        
        if rota_temp and len(rota_temp) > 1:
            proximo = rota_temp[1]
            # Pega a distância (sem o fator de trânsito) e o tempo (com trânsito)
            distancia = mapa_br.conexoes[simulacao_estado['local_atual']][proximo][0]
            tempo = mapa_br.calcular_tempo_real(simulacao_estado['local_atual'], proximo, simulacao_estado['veiculo'].velocidade_media)
            
            simulacao_estado['distancia_acumulada'] += distancia
            simulacao_estado['tempo_acumulado'] += tempo
            simulacao_estado['local_atual'] = proximo
            simulacao_estado['trajeto'].append(proximo)

            # Verifica e realiza as entregas no novo ponto
            entregues = [p for p in simulacao_estado['pedidos'] if p.destino == proximo]
            for p in entregues: simulacao_estado['pedidos'].remove(p)

    # 2. Se todos os pedidos foram entregues após o movimento
    if not simulacao_estado['pedidos']:
        simulacao_estado['ativo'] = False
        return jsonify({
            "status": "concluido", 
            "html_mapa": gerar_mapa_html(mapa_br, trajeto_feito=simulacao_estado['trajeto']),
            "trajeto_total": " -> ".join(simulacao_estado['trajeto']),
            "tempo_total": round(simulacao_estado['tempo_acumulado'], 2),
            "distancia_total": round(simulacao_estado['distancia_acumulada'], 2)
        })

    # 3. Recalcula a rota A PARTIR DA NOVA POSIÇÃO para mostrar no mapa e texto
    rota, custo = planejar_rota_a_star(simulacao_estado['local_atual'], simulacao_estado['veiculo'], simulacao_estado['pedidos'], mapa_br)
    if not rota: 
        return jsonify({"status": "erro", "msg": "Rota não encontrada!"})
    
    simulacao_estado['rota_atual'] = rota

    # Gera HTML do Mapa sincronizado
    mapa_html = gerar_mapa_html(mapa_br, rota_destaque=simulacao_estado['rota_atual'], trajeto_feito=simulacao_estado['trajeto'])
    
    # Pega conexões atuais para o select de trânsito
    conexoes = list(mapa_br.conexoes[simulacao_estado['local_atual']].keys())

    return jsonify({
        "status": "andamento",
        "local_atual": simulacao_estado['local_atual'],
        "tempo_acumulado": round(simulacao_estado['tempo_acumulado'], 2),
        "pedidos_restantes": len(simulacao_estado['pedidos']),
        "proxima_rota": " -> ".join(simulacao_estado['rota_atual']),
        "html_mapa": mapa_html,
        "vizinhos": conexoes
    })

@app.route('/api/transito', methods=['POST'])
def reportar_transito():
    dados = request.json
    origem = simulacao_estado['local_atual']
    destino = dados['destino']
    fator = float(dados['fator'])
    mapa_br.atualizar_transito(origem, destino, fator)
    
    # Recalcula a rota com o novo trânsito, sem mover o caminhão
    return avancar_passo(simular_apenas=True)

if __name__ == '__main__':
    app.run(debug=True)