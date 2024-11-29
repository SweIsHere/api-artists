import json
import boto3
import os

# Cliente de DynamoDB
dynamodb = boto3.resource('dynamodb')

# Obtener el nombre de la tabla desde las variables de entorno
ARTISTS_TABLE = os.environ['TABLE_NAME_ARTISTS']
table = dynamodb.Table(ARTISTS_TABLE)

def lambda_handler(event, context):
    # Obtener el cuerpo del evento (body)
    body = event.get('body', {})  # Si el body es un string, lo deserializamos
    
    # Validar encabezado Authorization
    token = event['headers'].get('Authorization')
    if not token:
        return {
            'statusCode': 400,
            'message': 'Falta el encabezado Authorization'
        }

    # Obtener artist_id del cuerpo
    artist_id = body.get('artist_id')
    if not artist_id:
        return {
            'statusCode': 400,
            'message': 'Falta el parámetro artist_id'
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

    # Continuar con la lógica si el token es válido
    try:
        # Extraer los datos necesarios para cambiar el username
        new_name = body.get('new_name')
        if new_name:
            new_name = new_name.strip().lower()
        
        # Validar que los parámetros requeridos estén presentes
        if not new_name:
            return {
                "statusCode": 400,
                "message": "Falta el parámetro 'new_name'"
            }
        
        # Buscar el usuario en la base de datos usando artist_id
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('artist_id').eq(artist_id)
        )
        
        # Verificar si el usuario existe
        if 'Items' not in response or len(response['Items']) == 0:
            return {
                "statusCode": 404,
                "message": "Usuario no encontrado"
            }

        # Obtener el primer usuario encontrado (asumimos que hay solo uno por artist_id)
        user = response['Items'][0]
        
        # Actualizar el username del usuario
        user['name'] = new_name
        
        # Actualizar el registro en DynamoDB
        table.put_item(Item=user)
        
        return {
            "statusCode": 200,
            "message": "Username actualizado exitosamente",
            "name": new_name
        }

    except Exception as e:
        # Manejo de errores
        print(f"Error al actualizar el username: {e}")
        return {
            "statusCode": 500,
            "message": "Error interno del servidor"
        }
