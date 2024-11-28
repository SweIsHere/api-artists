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
        token = event['headers'].get('Authorization')

        if not token:
            return {
                'statusCode': 400,
                'message': 'Falta el encabezado Authorization'
            }

        # Obtener artist_id del cuerpo de la solicitud
        artist_id = body.get('artist_id')
        if not artist_id:
            return {
                'statusCode': 400,
                'message': 'Falta el parámetro artist_id'
            }

        # Invocar el Lambda para validar el token
        lambda_client = boto3.client('lambda')
        payload = {
            "token": token,
            "artist_id": artist_id
        }

        # Invocar el Lambda ValidarTokenAcceso
        lambda_function_name = f"{os.environ['SERVICE_NAME']}-{os.environ['STAGE']}-ValidateToken_A"

        invoke_response = lambda_client.invoke(
            FunctionName=lambda_function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )

        # Leer la respuesta del Lambda invocado
        response = json.loads(invoke_response['Payload'].read())
        print(f"Respuesta de ValidarTokenAcceso: {response}")

        # Validar la respuesta del Lambda invocado
        if 'statusCode' not in response:
            return {
                'statusCode': 500,
                'message': 'Respuesta inválida de ValidarTokenAcceso'
            }

        # Manejar errores de validación de token
        if response['statusCode'] == 403:
            return {
                'statusCode': 403,
                'message': 'Forbidden - Acceso No Autorizado'
            }

        if response['statusCode'] == 401:
            return {
                'statusCode': 401,
                'message': 'Unauthorized - Token Expirado'
            }

        # Token válido, proceder con la consulta de usuario en DynamoDB
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
            "name": user.get("name")
        }

    except Exception as e:
        # Manejo de errores
        print(f"Error en Lambda: {e}")
        return {
            "statusCode": 500,
            "message": "Error interno del servidor",
            "error": str(e)
        }
