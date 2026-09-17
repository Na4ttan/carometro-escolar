import { Component, OnInit, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-root',
  imports: [],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App implements OnInit {
  // 1. Transforme as variáveis em Signals
  mensagem = signal('Carregando...');
  status = signal('');

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    console.log('Iniciando requisição para o Django...');

    this.http.get<{ mensagem: string; status: string }>(
      'http://127.0.0.1:8000/api/teste/'
    ).subscribe({
      next: (resposta) => {
        console.log('Resposta recebida da API:', resposta);

        // 2. Atualize o valor usando .set()
        this.mensagem.set(resposta.mensagem);
        this.status.set(resposta.status);
      },
      error: (erro) => {
        console.error('Erro ao consumir a API:', erro);

        this.mensagem.set('Não foi possível conectar à API Django.');
        this.status.set('erro');
      }
    });
  }
}