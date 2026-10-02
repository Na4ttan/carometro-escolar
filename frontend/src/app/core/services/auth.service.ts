import { Injectable, signal, computed, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { UsuarioPerfil } from '../../shared/models/usuario-perfil.model';
import { environment } from '../../environments/environment';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private http = inject(HttpClient);

  token = signal<string | null>(localStorage.getItem('token'));
  perfil = signal<UsuarioPerfil | null>(null);
  estaLogado = computed(() => !!this.token());

  login(username: string, password: string) {
    return this.http.post<{ token: string }>(`${environment.apiUrl}/auth/login/`, { username, password });
  }

  salvarToken(token: string) {
    this.token.set(token);
    localStorage.setItem('token', token);
  }

  carregarPerfil() {
    return this.http.get<UsuarioPerfil>(`${environment.apiUrl}/auth/perfil/`);
  }

  logout() {
    return this.http.post(`${environment.apiUrl}/auth/logout/`, {});
  }

  limparSessao() {
    this.token.set(null);
    this.perfil.set(null);
    localStorage.removeItem('token');
  }
}