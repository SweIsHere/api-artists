# API Artists

Este repositorio contiene una API para gestionar usuarios/artistas, incluyendo operaciones como el registro, inicio de sesión y modificación de datos. La API está construida usando AWS Lambda, API Gateway y DynamoDB.

## API Endpoints

### 1. **POST /users/register**
- **Descripción**: Registra un nuevo artista en la base de datos.
- **Parámetros**:
  - `artist_id`: ID único del artista.
  - `password`: Contraseña para el artista.
  - `country`: País del artista.
  - `name`: Nombre del artista.
  - `info`: Información adicional sobre el artista.
  
- **Respuesta**:
  - `200 OK`: Artista registrado exitosamente.
  - `400 Bad Request`: Parámetros faltantes (artist_id, password, country, name).
  
### 2. **POST /users/login**
- **Descripción**: Inicia sesión utilizando el `artist_id` y la `password` del artista.
- **Parámetros**:
  - `artist_id`: ID del artista.
  - `password`: Contraseña del artista.
  
- **Respuesta**:
  - `200 OK`: Token de acceso y refresh token generados.
  - `400 Bad Request`: Faltan parámetros necesarios.
  - `403 Forbidden`: Error al validar la contraseña.

### 3. **POST /users/change-info**
- **Descripción**: Cambia la información del artista (campo `info`).
- **Parámetros**:
  - `artist_id`: ID del artista.
  - `info`: Nueva información del artista.
  
- **Respuesta**:
  - `200 OK`: Información actualizada exitosamente.
  - `400 Bad Request`: Faltan parámetros necesarios.
  - `403 Forbidden`: Error al cambiar la información.

### 4. **GET /users/getByNameSCAN**
- **Descripción**: Obtiene un artista por nombre usando un `scan` en DynamoDB.
- **Parámetros**:
  - `name`: Nombre del artista.
  
- **Respuesta**:
  - `200 OK`: Artista encontrado.
  - `404 Not Found`: No se encontró el artista.

### 5. **POST /users/validate-token**
- **Descripción**: Valida un token de acceso de un artista.
- **Parámetros**:
  - `token`: Token de acceso generado previamente.
  - `artist_id`: ID del artista.
  
- **Respuesta**:
  - `200 OK`: Token válido.
  - `403 Forbidden`: Token expirado o inválido.
  - `401 Unauthorized`: No autorizado.

---

## `serverless.yml`

Este archivo es utilizado para desplegar la API utilizando Serverless Framework. Configura los recursos necesarios en AWS, como las funciones Lambda, las tablas DynamoDB y los índices secundarios globales (GSI).

### Estructura del archivo `serverless.yml`:

```yaml
org: angelt
service: api-users

provider:
  name: aws
  runtime: python3.12
  region: us-east-1
  stage: dev
  memorySize: 128
  timeout: 30
  iam:
    role: arn:aws:iam::542697993719:role/LabRole
  environment:
    TABLE_NAME_ARTISTS: ${self:provider.stage}-Pt_artists
    TABLE_NAME_TOKENS: ${self:provider.stage}-Pt_tokens_acceso

functions:
  registerUser:
    handler: registerUser.lambda_handler
    memorySize: 320
    events:
      - http:
          path: /users/register
          method: post
          cors: true
          integration: lambda

  loginUser:
    handler: loginUser.lambda_handler
    memorySize: 320
    events:
      - http:
          path: /users/login
          method: post
          cors: true
          integration: lambda

  changeInfo:
    handler: changeInfo.lambda_handler
    memorySize: 320
    events:
      - http:
          path: /users/change-info
          method: post
          cors: true
          integration: lambda

  getByNameSCAN:
    handler: getByNameSCAN.lambda_handler
    memorySize: 320
    events:
      - http:
          path: /users/getByNameSCAN
          method: post
          cors: true
          integration: lambda

resources:
  Resources:
    DynamoDbTableArtist:
      Type: 'AWS::DynamoDB::Table'
      Properties:
        AttributeDefinitions:
          - AttributeName: artist_id
            AttributeType: S
          - AttributeName: country
            AttributeType: S
          - AttributeName: name
            AttributeType: S
        KeySchema:
          - AttributeName: artist_id
            KeyType: HASH
        BillingMode: PAY_PER_REQUEST
        TableName: ${self:provider.environment.TABLE_NAME_ARTISTS}
        PointInTimeRecoverySpecification:
          PointInTimeRecoveryEnabled: true
        GlobalSecondaryIndexes:
          - IndexName: CountryIndex
            KeySchema:
              - AttributeName: country
                KeyType: HASH
            Projection:
              ProjectionType: ALL
            ProvisionedThroughput:
              ReadCapacityUnits: 1
              WriteCapacityUnits: 1
          - IndexName: NameTenantIndex
            KeySchema:
              - AttributeName: name
                KeyType: HASH
              - AttributeName: artist_id
                KeyType: RANGE
            Projection:
              ProjectionType: ALL
            ProvisionedThroughput:
              ReadCapacityUnits: 1
              WriteCapacityUnits: 1

    DynamoDbTableTokens:
      Type: 'AWS::DynamoDB::Table'
      Properties:
        AttributeDefinitions:
          - AttributeName: tenant_id
            AttributeType: S
          - AttributeName: token
            AttributeType: S
        KeySchema:
          - AttributeName: tenant_id
            KeyType: HASH
          - AttributeName: token
            KeyType: RANGE
        ProvisionedThroughput:
          ReadCapacityUnits: 1
          WriteCapacityUnits: 1
        TableName: ${self:provider.environment.TABLE_NAME_TOKENS}
        PointInTimeRecoverySpecification:
          PointInTimeRecoveryEnabled: true
