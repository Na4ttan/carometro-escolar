import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';
import { Escola } from '../../shared/models/escola.model';

@Injectable({ providedIn: 'root' })
export class EscolaService {
  private http = inject(HttpClient);

  buscar() {
    return this.http.get<Escola>(`${environment.apiUrl}/escola/`);
  }
}