## 📋 Checklist do Trabalho: Planejamento Inteligente de Rotas

### 1. Objetivo Principal
- [ ] Desenvolver sistema para planejar rotas de entrega eficientes.
- [ ] Otimizar o resultado: minimizar o tempo total de entrega OU o custo operacional.

### 2. Fatores e Restrições (Variáveis do Ambiente)
- [ ] Considerar o trânsito variável no cálculo das rotas.
- [ ] Implementar sistema de prioridades de entrega para os pacotes.
- [ ] Respeitar a capacidade máxima de carga dos veículos.
- [ ] Considerar as janelas de tempo (prazos específicos para cada entrega).

### 3. Comportamento Dinâmico (Execução em Tempo Real)
- [ ] Processar novos pedidos que surgem enquanto as rotas já estão em execução.
- [ ] Garantir que o sistema recalcule as rotas e se adapte dinamicamente às mudanças.

### 4. Modelagem e Algoritmo (O Núcleo da IA)
- [ ] Modelar o problema espacial e as rotas como um Grafo.
- [ ] Definir a estrutura dos Estados da busca (o estado deve armazenar: localização atual, carga do veículo e pedidos pendentes).
- [ ] Implementar o algoritmo de busca heurística **A*** (A-estrela) para encontrar os melhores caminhos.

### 5. Entrega Final
- [ ] Desenvolver e testar o protótipo funcional de ponta a ponta.


## Como Rodar o seu Software
1.  Abra o seu terminal/prompt de comando.
2.  Navegue até a pasta onde você salvou os dois arquivos.
3.  Digite o comando para ligar o servidor web:
    ```bash
    python app.py
    ```
4.  O terminal vai mostrar uma mensagem parecida com `Running on http://127.0.0.1:5000`.
5.  Abra o seu navegador (Chrome, Edge, etc.) e acesse **`http://127.0.0.1:5000Para transformar o seu projeto de um script no Jupyter Notebook para uma aplicação web real, precisamos mudar um pouco a arquitetura. Como a web funciona através de requisições e respostas (HTTP), o seu loop `while` infinito do terminal não vai funcionar no navegador.

A melhor e mais profissional forma de fazer isso para o seu TCC é dividir o projeto em duas partes:
1.  **Backend (Python + Flask):** Um servidor leve que vai hospedar o seu código A*, guardar o "estado" da simulação (onde o caminhão está) e processar as rotas.
2.  **Frontend (HTML + Bootstrap + JavaScript):** A interface onde você vai clicar nos botões e ver o mapa do Folium.

Aqui está a estrutura completa para você criar essa aplicação.

---

### 1. Preparando o Ambiente

Primeiro, você precisará instalar o **Flask**, que é o framework web para Python:
```bash
pip install flask