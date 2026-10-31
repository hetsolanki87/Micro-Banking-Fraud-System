
import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-deposit',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './deposit.component.html',
  styleUrl: './deposit.component.css'
})
export class DepositComponent {
  amount: number | null = null;
  loading = false;
  errorMessage = '';
  successMessage = '';
  balance: number | null = null;

  constructor(private http: HttpClient) {}

  setAmount(value: number): void {
    this.amount = value;
    this.errorMessage = '';
    this.successMessage = '';
  }

  depositMoney(): void {
    this.errorMessage = '';
    this.successMessage = '';

    if (this.amount === null || !Number.isFinite(this.amount) || this.amount <= 0) {
      this.errorMessage = 'Please enter a valid amount greater than zero.';
      return;
    }

    if (this.amount > 1000000) {
      this.errorMessage = 'For this demo, the maximum deposit is ₹10,00,000.';
      return;
    }

    const token = localStorage.getItem('access_token');

    if (!token) {
      this.errorMessage = 'Please log in before making a deposit.';
      return;
    }

    this.loading = true;

    const headers = new HttpHeaders({
      Authorization: `Bearer ${token}`
    });

    this.http.post<any>(
      'http://127.0.0.1:8000/transactions/deposit',
      { amount: this.amount },
      { headers }
    ).subscribe({
      next: (response) => {
        this.loading = false;
        this.successMessage =
          response?.message || 'Your deposit was completed successfully.';
        this.balance =
          response?.balance_after ??
          response?.new_balance ??
          response?.balance ??
          null;
        this.amount = null;
      },
      error: (error) => {
        this.loading = false;
        this.errorMessage =
          error.error?.detail || 'Deposit failed. Please try again.';
      }
    });
  }
}
