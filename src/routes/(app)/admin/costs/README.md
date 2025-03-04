# Página de Custos de Modelos

Esta página permite aos administradores visualizar o custo total de todos os modelos para todos os usuários.

## Funcionalidades

- Visualização do custo total de todos os modelos
- Visualização dos custos por modelo
- Visualização dos custos por usuário
- Detalhes de custos por modelo para cada usuário
- Detalhes de custos por usuário para cada modelo

## Implementação

A página calcula os custos com base nas informações de tokens armazenadas em cada mensagem. Os preços são definidos por modelo e são aplicados aos tokens de entrada (prompt) e saída (completion).

### Estrutura de Preços

Os preços são definidos por 1000 tokens e variam de acordo com o modelo. Os valores atuais são:

#### OpenAI
- GPT-4: €0,03 por 1000 tokens de entrada, €0,06 por 1000 tokens de saída
- GPT-4-32k: €0,06 por 1000 tokens de entrada, €0,12 por 1000 tokens de saída
- GPT-4-Turbo: €0,01 por 1000 tokens de entrada, €0,03 por 1000 tokens de saída
- GPT-4o: €0,01 por 1000 tokens de entrada, €0,03 por 1000 tokens de saída
- GPT-3.5-Turbo: €0,0015 por 1000 tokens de entrada, €0,002 por 1000 tokens de saída

#### Anthropic
- Claude-3-Opus: €0,015 por 1000 tokens de entrada, €0,075 por 1000 tokens de saída
- Claude-3-Sonnet: €0,003 por 1000 tokens de entrada, €0,015 por 1000 tokens de saída
- Claude-3-Haiku: €0,00025 por 1000 tokens de entrada, €0,00125 por 1000 tokens de saída

#### Modelos Locais (Ollama)
- Todos os modelos locais: €0 (gratuitos)

## Cálculo de Custos

O cálculo de custos é feito da seguinte forma:

1. Para cada chat de cada usuário, são analisadas todas as mensagens do assistente
2. Para cada mensagem, são extraídos os tokens de entrada e saída
3. O custo é calculado multiplicando o número de tokens pelo preço por 1000 tokens
4. Os custos são agregados por modelo e por usuário

## APIs Utilizadas

- `getAllUserChats`: Obtém todos os chats de todos os usuários
- `getUsers`: Obtém todos os usuários do sistema

## Permissões

Esta página só pode ser acessada por usuários com a função de administrador. 