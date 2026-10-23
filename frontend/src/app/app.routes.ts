import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  {
    path: 'login',
    loadComponent: () => import('./features/login/login.component').then(m => m.LoginComponent)
  },
  { path: 'inicio', redirectTo: 'consulta', pathMatch: 'full' },
  {
    path: 'consulta',
    canActivate: [authGuard],
    loadComponent: () => import('./features/consulta/consulta.component').then(m => m.ConsultaComponent)
  },
  {
    path: 'alunos/novo',
    canActivate: [authGuard],
    loadComponent: () => import('./features/aluno-form/aluno-form.component').then(m => m.AlunoFormComponent)
  },
  {
    path: 'professores/novo',
    canActivate: [authGuard],
    loadComponent: () => import('./features/professor-form/professor-form.component').then(m => m.ProfessorFormComponent)
  },
  {
    path: 'estrutura-academica',
    canActivate: [authGuard],
    loadComponent: () => import('./features/academico-form/academico-form.component').then(m => m.AcademicoFormComponent)
  },
  {
    path: 'tutorial',
    canActivate: [authGuard],
    loadComponent: () => import('./features/tutorial/tutorial.component').then(m => m.TutorialComponent)
  }
];
