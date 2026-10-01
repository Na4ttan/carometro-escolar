import { Component, OnInit, inject } from '@angular/core';
import { Router, RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from './core/services/auth.service';
import { TemaService } from './core/services/tema.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App implements OnInit {
  protected authService = inject(AuthService);
  protected temaService = inject(TemaService);
  private router = inject(Router);

  ngOnInit(): void {
    this.temaService.inicializar();
    if (this.authService.token()) {
      this.authService.carregarPerfil().subscribe({
        next: (perfil) => this.authService.perfil.set(perfil),
        error: () => this.authService.limparSessao(),
      });
    }
  }

  sair(): void {
    this.authService.logout().subscribe({
      next: () => this.finalizarSessao(),
      error: () => this.finalizarSessao(),
    });
  }

  private finalizarSessao(): void {
    this.authService.limparSessao();
    this.router.navigate(['/login']);
  }
}
