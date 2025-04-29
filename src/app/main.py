from fastapi import FastAPI, Depends, HTTPException, Query, Request
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from .database.connection import get_db_connection
from .auth.token import verify_token, create_access_token
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title="API Altervision", description="API para consulta de vendas")
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

class TokenData(BaseModel):
    username: str

class Token(BaseModel):
    access_token: str
    token_type: str

class VendaResponse(BaseModel):
    data: str
    hora: str
    nome: str
    cpf: str
    numVendas: int
    numItens: float
    valor: float

@app.post("/token", response_model=Token)
def login(username: str = Query(...)):
    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")))
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/vendas", response_model=list[VendaResponse])
@limiter.limit(os.getenv("RATE_LIMIT_PER_MINUTE", "60")+"/minute")
async def get_vendas(
    request: Request,
    cnpj: str,
    data_inicio: datetime,
    data_fim: datetime,
    token_data=Depends(verify_token)
):
    # Validação do intervalo de datas
    if (data_fim - data_inicio) > timedelta(days=31):
        raise HTTPException(
            status_code=400,
            detail="O intervalo entre as datas não pode ser maior que 31 dias"
        )

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
        SELECT
            DATE_FORMAT(mov.data_hora, '%Y-%m-%d') as data,
            DATE_FORMAT(mov.data_hora, '%H') as hora,
            u.nome,
            coalesce(u.CPF, 'Sem Cpf') as cpf,
            COUNT(DISTINCT numlanc) as numVendas,
            SUM(quanti_uni) as numItens,
            SUM(valor_tot) as valor
        FROM movment mov
        JOIN usuario u ON mov.usuario_id = u.usuario_id
        JOIN filial f ON mov.filial_id = f.filial_id
        WHERE mov.cancelado = "N"
        AND mov.apagado = "N"
        AND mov.oper IN (2, 3)
        AND ((mov.entrega = "N") OR (mov.dtchegada_entrega IS NOT NULL))
        AND mov.data_hora BETWEEN %s AND %s
        AND mov.produto_id NOT IN (8105081)
        AND f.cgc = %s
        GROUP BY 1,2,3,4
        """
        
        cursor.execute(query, (data_inicio, data_fim, cnpj))
        results = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return results

    except mysql.connector.Error as err:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao consultar o banco de dados: {str(err)}"
        )
