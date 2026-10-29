import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';
import { Turma } from '../../shared/models/turma.model';

export interface AnoLetivo {
  id: number;
  ano: number;
  data_inicio: string | null;
  data_fim: string | null;
  ativo: boolean;
}

export interface NovaTurma {
  ano_letivo: number;
  nivel_ensino: 'fundamental' | 'medio';
  serie: number;
  nome: string;
  turno: string;
  sala: string;
}

@Injectable({ providedIn: 'root' })
export class TurmaService {
  private http = inject(HttpClient);

  listar() {
    return this.http.get<Turma[]>(`${environment.apiUrl}/turmas/`);
  }

  listarAnosLetivos() {
    return this.http.get<AnoLetivo[]>(`${environment.apiUrl}/anos-letivos/`);
  }

  cadastrarAnoLetivo(dados: Omit<AnoLetivo, 'id'>) {
    return this.http.post<AnoLetivo>(`${environment.apiUrl}/anos-letivos/`, dados);
  }

  ativarAnoLetivo(id: number) {
    return this.http.post<AnoLetivo>(`${environment.apiUrl}/anos-letivos/${id}/ativar/`, {});
  }

  listarTurmasDoAno(anoLetivoId: number, incluirArquivadas = false) {
    return this.http.get<Turma[]>(`${environment.apiUrl}/turmas/`, {
      params: incluirArquivadas
        ? { ano_letivo: anoLetivoId, incluir_arquivadas: 'true' }
        : { ano_letivo: anoLetivoId },
    });
  }

  cadastrarTurma(dados: NovaTurma) {
    return this.http.post<Turma>(`${environment.apiUrl}/turmas/`, dados);
  }

  atualizarTurma(id: number, dados: Partial<NovaTurma>) {
    return this.http.patch<Turma>(`${environment.apiUrl}/turmas/${id}/`, dados);
  }

  arquivarTurma(id: number) {
    return this.http.post<Turma>(`${environment.apiUrl}/turmas/${id}/arquivar/`, {});
  }

  restaurarTurma(id: number) {
    return this.http.post<Turma>(`${environment.apiUrl}/turmas/${id}/restaurar/`, {});
  }

  excluirTurma(id: number) {
    return this.http.delete(`${environment.apiUrl}/turmas/${id}/`);
  }
}
