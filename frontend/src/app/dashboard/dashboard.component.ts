
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { RouterLink, RouterLinkActive } from '@angular/router';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css'
})
export class DashboardComponent implements OnInit {
  accountNumber = '';
  accountType = '';
  balance = 0;

  loading = true;
  errorMessage = '';

  recentTransactions: any[] = [];
  transactionsLoading = false;
  transactionsError = '';

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.loadAccount();
    this.loadRecentTransactions();
  }

  loadAccount(): void {
    const token = localStorage.getItem('access_token');

    if (!token) {
      this.errorMessage = 'Please login to access your account.';
      this.loading = false;
      return;
    }

    const headers = new HttpHeaders({
      Authorization: `Bearer ${token}`
    });

    this.http.get<any>(
      'http://127.0.0.1:8000/accounts/me',
      { headers }
    ).subscribe({
      next: (response) => {
        this.accountNumber = response.account_number;
        this.accountType = response.account_type;
        this.balance = response.balance;
        this.loading = false;
      },
      error: (error) => {
        console.error('Account loading error:', error);
        this.errorMessage =
          error.error?.detail ||
          'Unable to load account information.';
        this.loading = false;
      }
    });
  }

  loadRecentTransactions(): void {
    const token = localStorage.getItem('access_token');

    if (!token) {
      this.transactionsError = 'Please log in to view transactions.';
      return;
    }

    this.transactionsLoading = true;
    this.transactionsError = '';

    const headers = new HttpHeaders({
      Authorization: `Bearer ${token}`
    });

    this.http.get<any>(
      'http://127.0.0.1:8000/transactions/history',
      { headers }
    ).subscribe({
      next: (response) => {
        const items = Array.isArray(response)
          ? response
          : response?.transactions ??
            response?.history ??
            response?.data ??
            [];

        this.recentTransactions = Array.isArray(items)
          ? items.slice(0, 5)
          : [];

        this.transactionsLoading = false;
      },
      error: (error) => {
        console.error('Transaction loading error:', error);
        this.transactionsError =
          error.error?.detail ||
          'Could not load recent transactions.';
        this.transactionsLoading = false;
      }
    });
  }

  getTransactionType(transaction: any): string {
    return String(
      transaction?.transaction_type ??
      transaction?.type ??
      transaction?.transactionType ??
      'Transaction'
    );
  }

  getTransactionAmount(transaction: any): number {
    return Number(transaction?.amount ?? 0);
  }
  
getTransactionClass(transaction: any): string {
  const type = this.getTransactionType(transaction).toUpperCase();

  if (type.includes('DEPOSIT')) {
    return 'deposit-transaction';
  }

  if (type.includes('WITHDRAW')) {
    return 'withdraw-transaction';
  }

  if (type.includes('TRANSFER')) {
    return 'transfer-transaction';
  }

  return 'other-transaction';
}

getTransactionIcon(transaction: any): string {
  const type = this.getTransactionType(transaction).toUpperCase();

  if (type.includes('DEPOSIT')) {
    return '↓';
  }

  if (type.includes('WITHDRAW')) {
    return '↑';
  }

  if (type.includes('TRANSFER')) {
    return '⇄';
  }

  return '↔';
}

getTransactionPrefix(transaction: any): string {
  const type = this.getTransactionType(transaction).toUpperCase();

  if (type.includes('DEPOSIT')) {
    return '+';
  }

  if (type.includes('WITHDRAW')) {
    return '-';
  }

  return '';
}


  getTransactionDate(transaction: any): string {
    const value =
      transaction?.created_at ??
      transaction?.transaction_date ??
      transaction?.date;

    if (!value) {
      return 'Date unavailable';
    }

    const date = new Date(value);

    return Number.isNaN(date.getTime())
      ? 'Date unavailable'
      : date.toLocaleString();
  }

  logout(): void {
    localStorage.removeItem('access_token');
    window.location.href = '/';
  }
}
