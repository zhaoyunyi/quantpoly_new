/**
 * Contract Tests — 后端 API 响应结构契约校验（真实后端）
 *
 * 目标：
 * - 必须走后端 composition root 的真实响应（非 fixture/mock）
 * - 校验 envelope / 分页字段 / 关键 data 字段类型与前端类型对齐
 *
 * 覆盖端点：
 * - GET /users/me
 * - GET /strategies
 * - GET /backtests
 * - GET /trading/accounts
 * - GET /monitor/summary
 */

import { describe, it, expect, beforeAll } from 'vitest'
import type { SchemaSpec } from './schema-helpers'
import {
  validateSchema,
  assertSuccessEnvelope,
  assertErrorEnvelope,
  assertPagedData,
  PAGED_DATA_SPEC,
} from './schema-helpers'
import { loadBackendSnapshot, type BackendSnapshot } from './backend-snapshot'

/* ═══════════════════════════════════════════════════════════════
 * 各端点 data 字段 schema（对齐前端类型定义）
 * ═══════════════════════════════════════════════════════════════ */

const USER_PROFILE_SPEC: SchemaSpec = {
  id: { type: 'string' },
  email: { type: 'string' },
  displayName: { type: 'string', nullable: true },
  emailVerified: { type: 'boolean' },
  isActive: { type: 'boolean' },
  role: { type: 'string' },
  level: { type: 'number' },
}

const STRATEGY_ITEM_SPEC: SchemaSpec = {
  id: { type: 'string' },
  userId: { type: 'string' },
  name: { type: 'string' },
  template: { type: 'string' },
  parameters: { type: 'object' },
  status: { type: 'string' },
  createdAt: { type: 'string' },
  updatedAt: { type: 'string' },
}

const BACKTEST_TASK_SPEC: SchemaSpec = {
  id: { type: 'string' },
  userId: { type: 'string' },
  strategyId: { type: 'string' },
  status: { type: 'string' },
  config: { type: 'object' },
  // 前端类型要求 metrics 始终为对象（无指标时为 {}），不允许为 null
  metrics: { type: 'object' },
  displayName: { type: 'string', nullable: true },
  createdAt: { type: 'string' },
  updatedAt: { type: 'string' },
}

const TRADING_ACCOUNT_SPEC: SchemaSpec = {
  id: { type: 'string' },
  userId: { type: 'string' },
  accountName: { type: 'string' },
  isActive: { type: 'boolean' },
  createdAt: { type: 'string' },
}

const MONITOR_SUMMARY_SPEC: SchemaSpec = {
  type: { type: 'string' },
  generatedAt: { type: 'string' },
  metadata: { type: 'object' },
  accounts: { type: 'object' },
  strategies: { type: 'object' },
  backtests: { type: 'object' },
  tasks: { type: 'object' },
  signals: { type: 'object' },
  alerts: { type: 'object' },
  degraded: { type: 'object' },
  isEmpty: { type: 'boolean' },
}

let snapshot: BackendSnapshot

beforeAll(() => {
  snapshot = loadBackendSnapshot()
})

describe('contract_tests_real_backend', () => {
  describe('envelope_structure', () => {
    it('success_envelope_has_required_fields', () => {
      const { users_me, strategies, backtests, trading_accounts, monitor_summary } = snapshot.responses
      assertSuccessEnvelope(users_me.json)
      assertSuccessEnvelope(strategies.json)
      assertSuccessEnvelope(backtests.json)
      assertSuccessEnvelope(trading_accounts.json)
      assertSuccessEnvelope(monitor_summary.json)
    })

    it('error_envelope_has_required_fields', () => {
      const { unauth_strategies } = snapshot.responses
      expect(unauth_strategies.status).toBe(401)
      assertErrorEnvelope(unauth_strategies.json)
    })
  })

  describe('get_users_me', () => {
    it('response_data_matches_user_profile_schema', () => {
      const { users_me } = snapshot.responses
      expect(users_me.status).toBe(200)
      assertSuccessEnvelope(users_me.json, USER_PROFILE_SPEC)
    })
  })

  describe('get_strategies', () => {
    it('response_data_is_paged_with_strategy_items', () => {
      const { strategies } = snapshot.responses
      expect(strategies.status).toBe(200)

      assertSuccessEnvelope(strategies.json, PAGED_DATA_SPEC)
      const data = (strategies.json as { data: unknown }).data

      assertPagedData(data, STRATEGY_ITEM_SPEC)

      const d = data as { items: unknown[]; total: number }
      expect(Array.isArray(d.items)).toBe(true)
      expect(d.items.length).toBeGreaterThan(0)
      expect(d.total).toBeGreaterThan(0)
    })
  })

  describe('get_backtests', () => {
    it('response_data_is_paged_with_backtest_tasks', () => {
      const { backtests } = snapshot.responses
      expect(backtests.status).toBe(200)

      assertSuccessEnvelope(backtests.json, PAGED_DATA_SPEC)
      const data = (backtests.json as { data: unknown }).data

      assertPagedData(data, BACKTEST_TASK_SPEC)

      const d = data as { items: unknown[]; total: number }
      expect(Array.isArray(d.items)).toBe(true)
      expect(d.items.length).toBeGreaterThan(0)
      expect(d.total).toBeGreaterThan(0)
    })

    it('backtest_status_is_known_value', () => {
      const { backtests } = snapshot.responses
      const data = (backtests.json as { data: { items: Array<{ status: string }> } }).data
      const knownStatuses = ['pending', 'running', 'completed', 'failed', 'cancelled']
      for (const item of data.items) {
        expect(knownStatuses).toContain(item.status)
      }
    })

    it('metrics_is_object_and_not_null', () => {
      const { backtests } = snapshot.responses
      const data = (backtests.json as { data: { items: Array<{ metrics: unknown }> } }).data
      for (const item of data.items) {
        expect(typeof item.metrics).toBe('object')
        expect(item.metrics).not.toBeNull()
      }
    })
  })

  describe('get_trading_accounts', () => {
    it('response_data_is_array_of_accounts', () => {
      const { trading_accounts } = snapshot.responses
      expect(trading_accounts.status).toBe(200)

      assertSuccessEnvelope(trading_accounts.json)
      const data = (trading_accounts.json as { data: unknown }).data

      expect(Array.isArray(data)).toBe(true)
      const accounts = data as unknown[]
      expect(accounts.length).toBeGreaterThan(0)
      for (let i = 0; i < accounts.length; i++) {
        const errors = validateSchema(accounts[i], TRADING_ACCOUNT_SPEC, `accounts[${i}]`)
        expect(errors).toHaveLength(0)
      }
    })
  })

  describe('get_monitor_summary', () => {
    it('response_data_matches_monitor_summary_schema', () => {
      const { monitor_summary } = snapshot.responses
      expect(monitor_summary.status).toBe(200)
      assertSuccessEnvelope(monitor_summary.json, MONITOR_SUMMARY_SPEC)
    })
  })
})

