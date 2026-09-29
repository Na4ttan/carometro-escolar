import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';
import { Turma } from '../../shared/models/turma.model';

@Injectable({ providedIn: 'root' })
export class TurmaService {
  private http = inject(HttpClient);

  listar() {
    return this.http.get<Turma[]>(`${environment.apiUrl}/turmas/`);
  }
}