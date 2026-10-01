import { Injectable, signal } from "@angular/core";

type Tema = 'claro' | 'escuro';

@Injectable({ providedIn: 'root' })
export class TemaService {
  readonly tema = signal<Tema>(this.lerTema());

  inicializar(): void {
    this.aplicar(this.tema());
  }

  alternar(): void {
    this.aplicar(this.tema() === 'claro' ? 'escuro' : 'claro');
  }

  private aplicar(tema: Tema): void {
    this.tema.set(tema);
    document.documentElement.dataset['theme'] = tema;
    document.body.dataset['theme'] = tema;
    localStorage.setItem('carometro_tema', tema);
  }

  private lerTema(): Tema {
    const salvo = localStorage.getItem('carometro_tema');
    return salvo === 'escuro' ? 'escuro' : 'claro';
  }
}

