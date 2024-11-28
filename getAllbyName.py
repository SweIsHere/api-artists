import boto3
from boto3.dynamodb.conditions import Key
import os

# Cliente DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME_ARTISTS'])  # Obtén el nombre de la tabla desde las variables de entorno

def lambda_handler(event, context):
    # Obtener el 'name' del artista desde el evento
    # Obtener el cuerpo de la solicitud
    body = event['body']
    name = body.get('name')
    artist_id = body.get('artist_id')  # El 'artist_id' que se usa como sort key en el GSI

    if not name or not artist_id:
        return {
            'statusCode': 400,
            'body': 'Faltan los parámetros "name" o "artist_id"'
        }

    try:
        # Usamos el GSI 'NameArtistIdIndex' para buscar artistas por nombre 
        response = table.query(
            IndexName='NameArtistIdIndex',  # El nombre del índice GSI
            KeyConditionExpression=Key('name').eq(name) 
        )

        items = response.get('Items', [])

        if not items:
            return {
                'statusCode': 404,
                'body': 'No se encontraron artistas con el nombre proporcionados.'
            }

        return {
            'statusCode': 200,
            'body': {
                'message': 'Artistas encontrados.',
                'artists': items
            }
        }

    except Exception as e:
        print(f"Error al consultar los artistas: {e}")
        return {
            'statusCode': 500,
            'body': 'Error interno del servidor'
        }
