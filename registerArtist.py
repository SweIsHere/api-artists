import boto3
import hashlib
import json
import os  # Para acceder a las variables de entorno

# Hashear contraseña
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Función lambda que maneja el registro de usuario y validación de contraseña
def lambda_handler(event, context):
    try:
        # Imprimir el evento para depuración
        print("Received event:", json.dumps(event))

        # Obtener el nombre de la tabla desde las variables de entorno
        table_name = os.environ['TABLE_NAME_ARTISTS']
        print("Using DynamoDB table:", table_name)

        # Obtener el cuerpo del evento y verificar si necesita ser parseado
        if 'body' in event:
            # Si el cuerpo es una cadena JSON, lo parseamos a un diccionario
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = {}

        print("Parsed body:", json.dumps(body))

        # Extraer los campos necesarios del cuerpo
        artist_id = body.get('artist_id')
        password = body.get('password')
        country = body.get('country')
        name = body.get('name')
        info = body.get('info')

        # Verificar que todos los campos necesarios están presentes
        if not artist_id or not password or not country or not name:
            mensaje = {'error': 'Invalid request body: missing artist_id, password, country or name'}
            return {
                'statusCode': 400,
                'body': mensaje
            }

        # Normalizar el país ingresado (convertir a minúsculas y quitar espacios)
        country_input = country.strip().lower()

        # Si el país ingresado es vacío o contiene caracteres no válidos, retornar un error
        if not country_input.isalpha():
            mensaje = {'error': 'Invalid country, please enter a valid name'}
            return {'statusCode': 400, 'body': mensaje}

        # Hashea la contraseña antes de almacenarla
        hashed_password = hash_password(password)

        # Conectar a DynamoDB
        dynamodb = boto3.resource('dynamodb')
        t_usuarios = dynamodb.Table(table_name)  # Usar el nombre de la tabla desde el environment variable

        # Almacenar los datos del usuario en la tabla de usuarios en DynamoDB
        t_usuarios.put_item(
            Item={
                'artist_id': artist_id,
                'password': hashed_password,
                'country': country_input,
                'name': name,
                'info' : info,
                'photo': 'default-url'  # Valor por defecto para la foto
            }
        )

        # Retornar un código de estado HTTP 200 (OK) y un mensaje de éxito
        mensaje = {'message': 'User registered successfully', 'artist_id': artist_id}
        return {
            'statusCode': 200,
            'body': mensaje  # Convertir la respuesta a JSON
        }

    except Exception as e:
        # Excepción general y retornar un código de error HTTP 500
        print("Exception:", str(e))
        mensaje = {'error': str(e)}
        return {
            'statusCode': 500,
            'body': mensaje  # Convertir el mensaje de error a JSON
        }
