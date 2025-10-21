import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '../../services/auth.service';
import { AlertService } from '../../services/alert.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './login.html',
  styleUrl: './login.scss'
})
export class LoginComponent implements OnInit {
  loginForm: FormGroup;
  isLoading = false;
  errorMessage = '';

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router,
    private alertService: AlertService
  ) {
    this.loginForm = this.fb.group({
      username: ['', [Validators.required]],
      password: ['', [Validators.required]]
    });
  }

  ngOnInit() {
    // Si el usuario ya está autenticado, redirigir al dashboard
    this.authService.getCurrentUser().subscribe({
      next: (user) => {
        if (user) {
          console.log('Usuario ya autenticado, redirigiendo al dashboard');
          this.router.navigate(['/dashboard'], { replaceUrl: true });
        }
      }
    });

    // Prevenir navegación hacia atrás si hay una sesión activa
    window.history.pushState(null, '', window.location.href);
    window.onpopstate = () => {
      this.authService.getCurrentUser().subscribe({
        next: (user) => {
          if (user) {
            // Si hay sesión activa, mantener en dashboard
            window.history.pushState(null, '', window.location.href);
            this.router.navigate(['/dashboard'], { replaceUrl: true });
          }
        }
      });
    };
  }

  onSubmit() {
    if (this.loginForm.valid) {
      this.isLoading = true;
      this.errorMessage = '';
      console.log('Enviando credenciales:', this.loginForm.value);

      this.authService.login(this.loginForm.value).subscribe({
        next: (response) => {
          console.log('Login exitoso, redirigiendo al dashboard');
          this.isLoading = false;
          // Usar replaceUrl para que no se pueda volver con el botón atrás
          this.router.navigate(['/dashboard'], { replaceUrl: true });
        },
        error: (error) => {
          console.error('Error en login:', error);
          this.isLoading = false;

          // Verificar si el error es por usuario inactivo
          const errorDetail = error.error?.detail || 'Error al iniciar sesión';

          if (errorDetail.toLowerCase().includes('inactivo') || errorDetail.toLowerCase().includes('desactivado')) {
            this.alertService.error(
              'Tu cuenta ha sido desactivada. Por favor, contacta al administrador del sistema para más información.',
              'Cuenta Inactiva'
            );
          } else if (error.status === 401) {
            this.alertService.error(
              'El usuario o la contraseña son incorrectos. Por favor, verifica tus credenciales e intenta nuevamente.',
              'Credenciales Incorrectas'
            );
          } else {
            this.alertService.error(errorDetail, 'Error de Inicio de Sesión');
          }

          this.errorMessage = errorDetail;
        }
      });
    } else {
      console.log('Formulario inválido');
    }
  }
}
