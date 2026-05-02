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