
import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { RouterLink } from '@angular/router';

interface Transaction {
  id: number | string;
  type: string;
  amount: number;
  status: string;
  date: string;
  description: string;
  fraudScore: number;
}

@Component({
  selector: 'app-transactions',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './transactions.component.html',
  styleUrl: './transactions.component.css'
})
export class TransactionsComponent implements OnInit {
  private api = 'http://127.0.0.1:8000';

  transactions: Transaction[] = [];
  loading = true;
  errorMessage = '';
selectedTransaction: Transaction | null = null;
  searchTerm = '';
  statusFilter = 'ALL';

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.loadTransactions();
  }

  loadTransactions(): void {
    const token = localStorage.getItem('access_token');

    if (!token) {
      this.errorMessage = 'Please log in to view transactions.';
      this.loading = false;
      return;
    }

    const headers = new HttpHeaders({
      Authorization: `Bearer ${token}`
    });

    this.loading = true;
    this.errorMessage = '';

    this.http.get<any>(
      `${this.api}/transactions/admin/all-transactions`,
      { headers }
    ).subscribe({
      next: (response) => {
        const records = Array.isArray(response)
          ? response
          : response?.transactions ?? [];

        this.transactions = records.map(
          (item: any, index: number): Transaction => ({
            id: item.transaction_id ?? item.id ?? index + 1,
            type: item.transaction_type ?? 'Transaction',
            amount: Number(item.amount ?? 0),
            status: item.status ?? 'Unknown',
            date: item.created_at ?? '',
            description:
              `Sender: ${item.sender_account_id ?? '-'} | ` +
              `Receiver: ${item.receiver_account_id ?? '-'}`,
            fraudScore: Number(item.fraud_score ?? 0)
          })
        );

        this.loading = false;
      },
      error: (error) => {
        console.error('Admin transaction history error:', error);

        this.errorMessage =
          error.error?.detail ??
          'Unable to load transactions. Please check your admin login.';

        this.loading = false;
      }
    });
  }

  get filteredTransactions(): Transaction[] {
    const query = this.searchTerm.trim().toLowerCase();

    return this.transactions.filter((transaction) => {
      const searchableText = [
        transaction.id,
        transaction.type,
        transaction.status,
        transaction.description
      ].join(' ').toLowerCase();

      const matchesSearch =
        !query || searchableText.includes(query);

      const matchesStatus =
        this.statusFilter === 'ALL' ||
        transaction.status.toUpperCase() === this.statusFilter;

      return matchesSearch && matchesStatus;
    });
  }

  getRiskLevel(score: number): string {
    if (score >= 70) {
      return 'HIGH';
    }

    if (score >= 30) {
      return 'MEDIUM';
    }

    return 'LOW';
  }

  countByStatus(status: string): number {
    return this.transactions.filter(
      transaction => transaction.status.toUpperCase() === status
    ).length;
  }

  countHighRisk(): number {
    return this.transactions.filter(
      transaction => transaction.fraudScore >= 70
    ).length;
  }

  getAccountDescription(
    description: string,
    accountType: string
  ): string {
    const match = description.match(
      new RegExp(`${accountType}:\\s*([^|]+)`, 'i')
    );

    return match
      ? `${accountType}: ${match[1].trim()}`
      : `${accountType}: —`;
  }

  formatCurrency(value: number): string {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 2
    }).format(value);
  }
}
