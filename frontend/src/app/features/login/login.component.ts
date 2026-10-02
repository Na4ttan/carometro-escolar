import { Component, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [FormsModule],
  templateUrl: 'login.component.html',
  styleUrl: 'login.component.css'
})
export class LoginComponent {
  private authService = inject(AuthService);
  private router = inject(Router);

  username = signal('');
  password = signal('');
  erro = signal('');

  async entrar() {
    this.authService.login(this.username(), this.password()).subscribe({
      next: ({ token }) => {
        this.authService.salvarToken(token);
        this.authService.carregarPerfil().subscribe({
          next: (perfil) => {
            this.authService.perfil.set(perfil);
            this.router.navigate([perfil.tipo === 'professor' ? '/consulta' : '/inicio']);
          },
          error: () => this.erro.set('Não foi possível carregar o perfil.')
        });
      },
      error: () => this.erro.set('Usuário ou senha inválidos')
    });
  }
}
