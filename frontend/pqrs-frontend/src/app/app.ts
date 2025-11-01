import { Component, computed, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterOutlet } from '@angular/router';
import { GlobalNavbarComponent } from './components/layout/global-navbar/global-navbar';

@Component({
  selector: 'app-root',
  imports: [CommonModule, RouterOutlet, GlobalNavbarComponent],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  protected readonly title = signal('pqrs-frontend');
  private router = inject(Router);

  get showGlobalNav() {
    const url = this.router.url;
    // Ocultar en rutas públicas y portal ciudadano/login/ventanilla
    if (/\/portal-ciudadano\b/.test(url)) return false;
    if (/\/login\b/.test(url)) return false;
    if (/^\/[\w-]+\/?$/.test(url)) return false; // ventanilla (root de entidad)
    if (/^\/showcase\b/.test(url)) return false;
    if (/^\/soft-admin\b/.test(url)) return false;
    return true;
  }
}
