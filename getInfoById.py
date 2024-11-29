import boto3
import json
import os
from boto3.dynamodb.conditions import Key

# Cliente de DynamoDB
dynamodb = boto3.resource('dynamodb')

# Obtener los nombres de las tablas desde las variables de entorno
ARTIST_TABLE = os.environ['TABLE_NAME_ARTISTS']
TOKENS_TABLE = os.environ['TABLE_NAME_TOKENS']

# Inicializar las tablas
artists_table = dynamodb.Table(ARTIST_TABLE)
tokens_table = dynamodb.Table(TOKENS_TABLE)

def lambda_handler(event, context):
    try:
        # Obtener los datos del evento
        body = event.get('body', {})
       
        # Obtener artist_id del cuerpo de la solicitud
        artist_id = body.get('artist_id')
        if not artist_id:
            return {
                'statusCode': 400,
                'message': 'Falta el parámetro artist_id'
            }

       
        dynamo_response = artists_table.query(
            KeyConditionExpression=Key('artist_id').eq(artist_id)
        )

        items = dynamo_response.get('Items', [])
        if not items:
            return {
                "statusCode": 404,
                "message": "Usuario no encontrado"
            }

        # Retornar información del usuario
        user = items[0]
        return {
            "statusCode": 200,
            "photo": user.get("photo"),
            "name": user.get("name"),
            "info":user.get("info")
        }

    except Exception as e:
        # Manejo de errores
        print(f"Error en Lambda: {e}")
        return {
            "statusCode": 500,
            "message": "Error interno del servidor",
            "error": str(e)
        }
