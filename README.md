# API Altervision

API para consulta de vendas com autenticação por token e rate limiting.

## Configuração

1. Clone o repositório
2. Crie um ambiente virtual Python:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
```
Edite o arquivo `.env` com suas configurações.

## Executando a API

```bash
uvicorn src.app.main:app --reload
```

A API estará disponível em `http://localhost:8000`

## Documentação da API

A documentação automática está disponível em:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoints

### POST /token

Gera um token de acesso.

**Parâmetros:**
- username (string, query): Nome do usuário

**Resposta:**
```json
{
    "access_token": "string",
    "token_type": "bearer"
}
```

### GET /vendas

Retorna dados de vendas.

**Parâmetros:**
- cnpj (string, query): CNPJ da filial
- data_inicio (datetime, query): Data inicial (formato: YYYY-MM-DD HH:MM:SS)
- data_fim (datetime, query): Data final (formato: YYYY-MM-DD HH:MM:SS)

**Headers necessários:**
- Authorization: Bearer {token}

**Resposta:**
```json
[
    {
        "data": "YYYY-MM-DD",
        "hora": "HH",
        "nome": "string",
        "cpf": "string",
        "numVendas": 0,
        "numItens": 0,
        "valor": 0
    }
]
```

## Limitações

- O intervalo entre data_inicio e data_fim não pode ser maior que 31 dias
- Rate limit: 60 requisições por minuto por IP
- Token expira em 30 minutos
