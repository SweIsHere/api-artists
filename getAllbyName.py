import boto3
from boto3.dynamodb.conditions import Key
import os

# Cliente DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME_ARTISTS'])  # Obtén el nombre de la tabla desde las variables de entorno

def lambda_handler(event, context):
    # Obtener el 'name' del artista desde el evento
    body = event['body']
    name = body.get('name')

    if not name:
        return {
            'statusCode': 400,
            'body': 'Faltan los parámetros "name"'
        }

    # Normalizar el nombre a minúsculas
    name = name.strip().lower()

    try:
        # Intentar usar query con el GSI 'NameArtistIdIndex'
        response = table.query(
            IndexName='NameArtistIdIndex',  # El nombre del índice GSI
            KeyConditionExpression=Key('name').eq(name)
        )

        items = response.get('Items', [])

        # Si no se encuentran resultados con query, hacer un scan
        if not items:
            print("No se encontraron resultados con query, usando scan...")
            response = table.scan(
                FilterExpression="contains(#name, :name_value)",
                ExpressionAttributeNames={
                    "#name": "name"  # Referencia a 'name' en la tabla
                },
                ExpressionAttributeValues={
                    ":name_value": name  # El valor de búsqueda para 'name'
                }
            )

            items = response.get('Items', [])

        if not items:
            return {
                'statusCode': 404,
                'body': 'No se encontraron artistas con el nombre proporcionado.'
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
