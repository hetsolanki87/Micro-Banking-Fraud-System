
import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

interface LoginResponse {
  access_token: string;
  token_type: string;
  role?: string;
}

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './home.component.html',
  styleUrl: './home.component.css'
})
export class HomeComponent {
  showLogin = false;
  showSignup = false;

  loginEmail = '';
  loginPassword = '';

  signupName = '';
  signupEmail = '';
  signupPassword = '';

  signupMessage = '';
  signupError = '';

  constructor(
    private http: HttpClient,
    private router: Router
  ) {}

  openLogin(): void {
    this.showSignup = false;
    this.showLogin = true;
  }

  openSignup(): void {
    this.showLogin = false;
    this.showSignup = true;
  }

  closeModal(): void {
    this.showLogin = false;
    this.showSignup = false;
  }

  switchToSignup(): void {
    this.showLogin = false;
    this.showSignup = true;
  }

  switchToLogin(): void {
    this.showSignup = false;
    this.showLogin = true;
  }

  // LOGIN
  onLogin(): void {
    const loginData = new URLSearchParams();
    loginData.set('username', this.loginEmail.trim());
    loginData.set('password', this.loginPassword);

    this.http.post<LoginResponse>(
      'http://127.0.0.1:8000/auth/login',
      loginData.toString(),
      {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      }
    ).subscribe({
      next: (response) => {
        console.log('LOGIN RESPONSE:', response);

        const role = String(response.role ?? '')
          .trim()
          .toUpperCase();

        console.log('DETECTED ROLE:', role);

        if (!response.access_token) {
          alert('Login response did not contain an access token.');
          return;
        }

        if (role !== 'ADMIN' && role !== 'USER') {
          alert(
            'Login succeeded, but the role is missing or invalid. Check the backend response.'
          );
          return;
        }

        localStorage.setItem(
          'access_token',
          response.access_token
        );
        localStorage.setItem('user_role', role);

        console.log(
          'SAVED ROLE:',
          localStorage.getItem('user_role')
        );

        this.closeModal();
        this.loginPassword = '';

        const destination =
  role === 'ADMIN' ? '/admin' : '/dashboard';

        console.log('NAVIGATING TO:', destination);

        this.router.navigateByUrl(destination).then(
          (success) => {
            console.log('NAVIGATION SUCCESS:', success);
            console.log('CURRENT ROUTER URL:', this.router.url);

            if (!success) {
              alert(
                `Navigation to ${destination} failed. Check app.routes.ts.`
              );
            }
          }
        ).catch((error) => {
          console.error('Navigation error:', error);
        });
      },

      error: (error) => {
        console.error('Login error:', error);

        if (error.error?.detail) {
          alert(error.error.detail);
        } else {
          alert(
            'Unable to log in. Please check your credentials and backend.'
          );
        }
      }
    });
  }

  // SIGNUP
  onSignup(): void {
    this.signupMessage = '';
    this.signupError = '';

    const signupData = {
      name: this.signupName.trim(),
      email: this.signupEmail.trim(),
      password: this.signupPassword
    };

    this.http.post(
      'http://127.0.0.1:8000/users/',
      signupData
    ).subscribe({
      next: () => {
        this.signupMessage =
          'Account created successfully! Please login.';

        this.signupName = '';
        this.signupEmail = '';
        this.signupPassword = '';
      },

      error: (error) => {
        console.error('Signup error:', error);

        if (error.error?.detail) {
          this.signupError = error.error.detail;
        } else {
          this.signupError =
            'Unable to create account. Please try again.';
        }
      }
    });
  }
}
