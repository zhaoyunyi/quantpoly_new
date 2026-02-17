/**
 * Contract Test — 轻量级 schema 校验辅助
 *
 * 用于验证后端 API 响应结构是否与前端类型定义一致。
 * 不依赖外部 JSON-schema 库，仅做字段存在性 + 基本类型校验。
 */

/* ─── 基础类型守卫 ─── */

export type PrimitiveType =
  | 'string'
  | 'number'
  | 'boolean'
  | 'object'
  | 'array'
  | 'null'

export interface FieldSpec {
  /** 字段对应的 JS 类型（typeof / Array.isArray） */
  type: PrimitiveType | PrimitiveType[]
  /** 是否可选（undefined / 缺失） */
  optional?: boolean
  /** 是否可为 null（显式 null 值） */
  nullable?: boolean
}

export type SchemaSpec = Record<string, FieldSpec>

/**
 * 校验 `obj` 的每个字段是否符合 `spec` 声明。
 * 返回所有不符项的描述列表；空数组 = 全部通过。
 */
export function validateSchema(
  obj: unknown,
  spec: SchemaSpec,
  path = '',
): string[] {
  const errors: string[] = []

  if (typeof obj !== 'object' || obj === null) {
    errors.push(`${path || 'root'}: expected object, got ${obj === null ? 'null' : typeof obj}`)
    return errors
  }

  const record = obj as Record<string, unknown>

  for (const [key, field] of Object.entries(spec)) {
    const fullPath = path ? `${path}.${key}` : key
    const value = record[key]

    // 缺失检查
    if (value === undefined) {
      if (!field.optional) {
        errors.push(`${fullPath}: missing required field`)
      }
      continue
    }

    // null 检查
    if (value === null) {
      if (!field.nullable) {
        errors.push(`${fullPath}: unexpected null`)
      }
      continue
    }

    // 类型检查
    const allowedTypes = Array.isArray(field.type) ? field.type : [field.type]
    const actualType = Array.isArray(value) ? 'array' : typeof value

    if (!allowedTypes.includes(actualType as PrimitiveType)) {
      errors.push(
        `${fullPath}: expected ${allowedTypes.join('|')}, got ${actualType}`,
      )
    }
  }

  return errors
}

/* ─── 公共信封结构 ─── */

export const SUCCESS_ENVELOPE_SPEC: SchemaSpec = {
  success: { type: 'boolean' },
  message: { type: 'string' },
  data: { type: ['object', 'array', 'string', 'number', 'boolean'], optional: true },
}

export const ERROR_ENVELOPE_SPEC: SchemaSpec = {
  success: { type: 'boolean' },
  error: { type: 'object' },
}

export const ERROR_DETAIL_SPEC: SchemaSpec = {
  code: { type: 'string' },
  message: { type: 'string' },
}

export const PAGED_DATA_SPEC: SchemaSpec = {
  items: { type: 'array' },
  total: { type: 'number' },
  page: { type: 'number' },
  pageSize: { type: 'number' },
}

/**
 * 验证成功信封包裹：{ success: true, message, data }
 * 并对 data 应用 dataSpec 校验。
 */
export function assertSuccessEnvelope(
  envelope: unknown,
  dataSpec?: SchemaSpec,
): void {
  const envErrors = validateSchema(envelope, SUCCESS_ENVELOPE_SPEC)
  if (envErrors.length > 0) {
    throw new Error(`success envelope 校验失败:\n  ${envErrors.join('\n  ')}`)
  }

  const env = envelope as { success: boolean; data?: unknown }
  if (!env.success) {
    throw new Error('envelope.success should be true')
  }

  if (dataSpec) {
    if (env.data === undefined) {
      throw new Error('success envelope missing required data field')
    }
    const dataErrors = validateSchema(env.data, dataSpec)
    if (dataErrors.length > 0) {
      throw new Error(`data 字段校验失败:\n  ${dataErrors.join('\n  ')}`)
    }
  }
}

/**
 * 验证错误信封：{ success: false, error: { code, message } }
 */
export function assertErrorEnvelope(envelope: unknown): void {
  const envErrors = validateSchema(envelope, ERROR_ENVELOPE_SPEC)
  if (envErrors.length > 0) {
    throw new Error(`error envelope 校验失败:\n  ${envErrors.join('\n  ')}`)
  }

  const env = envelope as { success: boolean; error?: unknown }
  if (env.success !== false) {
    throw new Error('envelope.success should be false')
  }

  const detailErrors = validateSchema(env.error, ERROR_DETAIL_SPEC)
  if (detailErrors.length > 0) {
    throw new Error(`error.detail 校验失败:\n  ${detailErrors.join('\n  ')}`)
  }
}

/**
 * 验证分页数据结构：{ items: [], total, page, pageSize }
 */
export function assertPagedData(
  data: unknown,
  itemSpec?: SchemaSpec,
): void {
  const pagedErrors = validateSchema(data, PAGED_DATA_SPEC)
  if (pagedErrors.length > 0) {
    throw new Error(`paged data 校验失败:\n  ${pagedErrors.join('\n  ')}`)
  }

  if (itemSpec) {
    const d = data as { items: unknown[] }
    for (let i = 0; i < d.items.length; i++) {
      const itemErrors = validateSchema(d.items[i], itemSpec, `items[${i}]`)
      if (itemErrors.length > 0) {
        throw new Error(`paged item[${i}] 校验失败:\n  ${itemErrors.join('\n  ')}`)
      }
    }
  }
}
