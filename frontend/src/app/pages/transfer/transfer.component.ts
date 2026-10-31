
import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-transfer',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './transfer.component.html',
  styleUrl: './transfer.component.css'
})
export class TransferComponent {
  receiverAccountNumber = '';
  amount: number | null = null;
  loading = false;
  errorMessage = '';
  successMessage = '';
  responseData: any = null;

  constructor(private http: HttpClient) {}

  setAmount(value: number): void {
    this.amount = value;
    this.errorMessage = '';
    this.successMessage = '';
  }

  transferMoney(): void {
    this.errorMessage = '';
    this.successMessage = '';
    this.responseData = null;

    const receiver = this.receiverAccountNumber.trim();

    if (!/^\d{10}$/.test(receiver)) {
      this.errorMessage = 'Enter a valid 10-digit receiver account number.';
      return;
    }

    if (
      this.amount === null ||
      !Number.isFinite(this.amount) ||
      this.amount <= 0
    ) {
      this.errorMessage = 'Enter an amount greater than zero.';
      return;
    }

    if (this.amount > 1000000) {
      this.errorMessage = 'The maximum transfer for this demo is ₹10,00,000.';
      return;
    }

    const token = localStorage.getItem('access_token');

    if (!token) {
      this.errorMessage = 'Please log in before transferring money.';
      return;
    }

    this.loading = true;

    const headers = new HttpHeaders({
      Authorization: `Bearer ${token}`
    });

    this.http.post<any>(
      'http://127.0.0.1:8000/transactions/transfer',
      {
        receiver_account_number: receiver,
        amount: this.amount
      },
      { headers }
    ).subscribe({
      next: (response) => {
        this.loading = false;
        this.successMessage =
          response?.message || 'Transfer completed successfully.';
        this.responseData = response;
        this.amount = null;
        this.receiverAccountNumber = '';
      },
      error: (error) => {
        this.loading = false;
        this.errorMessage =
          error.error?.detail ||
          'Transfer failed. Please check the details and try again.';
      }
    });
  }
}
 