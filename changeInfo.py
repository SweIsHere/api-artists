import boto3
import json
import os

# Cliente de DynamoDB
dynamodb = boto3.resource('dynamodb')

# Obtener el nombre de la tabla desde las variables de entorno
ARTIST_TABLE = os.environ['TABLE_NAME_ARTISTS']
table = dynamodb.Table(ARTIST_TABLE)

def lambda_handler(event, context):
    try:
        # Imprimir el evento recibido para depuración
        print(f"Evento recibido: {json.dumps(event, indent=2)}")

        # Obtener encabezados de la solicitud de manera segura
        headers = event.get('headers', {})
        token = headers.get('Authorization')
        
        if not token:
            return {
                'statusCode': 400,
                'message': 'Falta el encabezado Authorization'
            }

        # Obtener el cuerpo de la solicitud
        body = event['body']
        # Obtener artist_id y nuevo info del cuerpo
        artist_id = body.get('artist_id')
        new_info = body.get('info')

        if not artist_id:
            return {
                'statusCode': 400,
                'message': 'Falta el parámetro artist_id'
            }

        if not new_info:
            return {
                'statusCode': 400,
                'message': 'Falta el parámetro info'
            }

        # Crear el cliente de Lambda para invocar el Lambda de ValidarTokenAcceso
        lambda_client = boto3.client('lambda')

        # Crear el payload como JSON para validar el token
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

        # Si el token es válido, proceder con la actualización de la info
        # Consultar el artista en la base de datos usando artist_id
        response = table.get_item(
            Key={'artist_id': artist_id}
        )

        if 'Item' not in response:
            return {
                'statusCode': 404,
                'message': f'El artista con id {artist_id} no existe.'
            }

        # Actualizar solo el campo 'info' del artista
        table.update_item(
            Key={'artist_id': artist_id},
            UpdateExpression="SET info = :new_info",
            ExpressionAttributeValues={
                ':new_info': new_info
            }
        )

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Información del artista actualizada correctamente.'})
        }

    except Exception as e:
        # Manejo de errores
        print(f"Error al actualizar la información del artista: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Error interno del servidor.'})
        }
