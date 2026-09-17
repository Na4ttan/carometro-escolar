from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def teste_api(request):
    return Response({
        'mensagem': 'API do Carômetro funcionando!',
        'status': 'ok'
    })