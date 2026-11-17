<template>
  <div class="page" v-loading="loading">
    <div class="page-head">
      <div>
        <div class="page-kicker">AGENT GOVERNANCE</div>
        <h1 class="page-title">AI 协作监管</h1>
        <p class="page-sub">
          以 L1/L2/L3 分级管理 Agent 任务，用五维失效分量化可靠性，并将缺陷帕累托与失效复盘纳入维护闭环。
        </p>
      </div>
      <div class="page-actions">
        <el-button :icon="Refresh" @click="loadAll">刷新</el-button>
        <el-button v-if="isAdmin()" type="primary" :icon="Plus" @click="openTaskCreate">
          登记 AI 任务
        </el-button>
      </div>
    </div>

    <div class="panel tabs-panel">
      <el-tabs v-model="activeTab">
        <el-tab-pane label="可靠性总览" name="overview">
          <div class="tab-body">
            <div class="kpi-grid overview-kpis">
              <StatCard
                label="综合协作可靠性"
                :value="summary.reliability"
                unit="分"
                icon="DataLine"
                tone="gold"
                :hint="`0.6×(100−平均失效分)+0.4×一次通过率`"
              />
              <StatCard
                label="平均失效分"
                :value="summary.avg_failure_score"
                unit="分"
                icon="Warning"
                :hint="`${summary.task_count} 项任务 · ${summary.high_failure_count} 项高失效`"
              />
              <StatCard
                label="Agent 一次通过率"
                :value="summary.success_rate"
                unit="%"
                icon="CircleCheck"
                tone="green"
                :hint="`人工介入 ${summary.human_minutes} 分钟 · 重试 ${summary.retry_count} 次`"
              />
              <StatCard
                label="缺陷累计发生"
                :value="summary.defect_occurrences"
                unit="次"
                icon="Aim"
                tone="teal"
                :hint="`AI 相关 ${summary.ai_related_rate}% · 待修复 ${summary.open_rate}%`"
              />
            </div>

            <div class="grid-2">
              <div class="panel inner-panel">
                <div class="panel-head">
                  <div class="panel-title">各阶段平均失效分</div>
                  <div class="panel-note">虚线为 20 / 40 / 60 分阈值</div>
                </div>
                <div class="chart-body">
                  <ChartPanel :option="phaseOption" :height="300" :empty="!stats" />
                </div>
              </div>
              <div class="panel inner-panel">
                <div class="panel-head">
                  <div class="panel-title">任务等级与状态</div>
                  <div class="panel-note">共 {{ summary.task_count }} 项</div>
                </div>
                <div class="chart-body">
                  <ChartPanel :option="levelOption" :height="216" :empty="!stats" />
                </div>
                <div class="status-bars">
                  <div v-for="item in statusRows" :key="item.status" class="status-row">
                    <span>{{ AI_STATUS[item.status]?.label || item.status }}</span>
                    <div class="status-track">
                      <i :style="{ width: statusPercent(item) + '%' }" :class="item.status.toLowerCase()"></i>
                    </div>
                    <strong class="num">{{ item.count }}</strong>
                  </div>
                </div>
              </div>
            </div>

            <div class="panel inner-panel">
              <div class="panel-head">
                <div class="panel-title">高失效任务与复盘要点</div>
                <div class="panel-note">FS ≥ 40 需人工复核或升级处理</div>
              </div>
              <div class="table-wrap">
                <el-table :data="stats?.failure_cases || []" size="small">
                  <el-table-column prop="task_name" label="任务" min-width="210" show-overflow-tooltip />
                  <el-table-column label="阶段" width="100">
                    <template #default="{ row }">
                      <span class="muted">{{ AI_PHASE[row.phase] }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="等级" width="86">
                    <template #default="{ row }"><StatusPill kind="aiLevel" :value="row.level" /></template>
                  </el-table-column>
                  <el-table-column label="失效分" width="160">
                    <template #default="{ row }">
                      <div class="score-bar">
                        <div class="score-track"><i :style="{ width: `${row.failure_score}%` }"></i></div>
                        <strong class="num">{{ row.failure_score }}</strong>
                      </div>
                    </template>
                  </el-table-column>
                  <el-table-column label="等级判定" width="100">
                    <template #default="{ row }">
                      <span class="band" :class="row.failure_band.level.toLowerCase()">
                        {{ row.failure_band.label }}
                      </span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="retries" label="重试" width="62" align="center" />
                  <el-table-column prop="human_minutes" label="人工分钟" width="84" align="center" />
                  <el-table-column prop="notes" label="复盘要点" min-width="250" show-overflow-tooltip />
                </el-table>
              </div>
            </div>

            <div class="grid-2-even">
              <div class="panel inner-panel">
                <div class="panel-head">
                  <div class="panel-title">五维评分权重</div>
                  <div class="panel-note">Σ 权重 = 100%</div>
                </div>
                <div class="table-wrap">
                  <el-table :data="grading?.rubric || []" size="small">
                    <el-table-column prop="name" label="维度" width="112" />
                    <el-table-column label="权重" width="76">
                      <template #default="{ row }"><span class="num">{{ row.weight }}%</span></template>
                    </el-table-column>
                    <el-table-column prop="hint" label="评分说明" min-width="220" show-overflow-tooltip />
                  </el-table>
                </div>
              </div>
              <div class="panel inner-panel">
                <div class="panel-head">
                  <div class="panel-title">失效分阈值与处置</div>
                  <div class="panel-note">FS 越高，AI 产物越不可采信</div>
                </div>
                <div class="threshold-list">
                  <div
                    v-for="item in grading?.thresholds || []"
                    :key="item.level"
                    class="threshold-item"
                    :class="item.level.toLowerCase()"
                  >
                    <span class="threshold-range num">{{ item.min }}–{{ item.max }}</span>
                    <div>
                      <strong>{{ item.label }}</strong>
                      <p>{{ item.action }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="formula-box">
              <div class="formula-label">评分口径（系统与文档保持一致）</div>
              <div class="formula">{{ stats?.formula || '—' }}</div>
              <p>
                其中 C/I/R/M/S 为正确性、完整性、可运行性、可维护性、合规与安全五个维度的失效率评分（0–5，越高越差）。
                阶段综合可靠性按 0.6 的失效分权重与 0.4 的一次通过率权重合成。
              </p>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="AI 任务台账" name="tasks">
          <div class="filter-bar">
            <el-input
              v-model="taskQuery.q"
              placeholder="搜索任务名称 / Agent"
              clearable
              style="width: 230px"
              :prefix-icon="Search"
              @keyup.enter="searchTasks"
              @clear="searchTasks"
            />
            <el-select v-model="taskQuery.phase" placeholder="阶段" clearable style="width: 130px" @change="searchTasks">
              <el-option v-for="(label, key) in AI_PHASE" :key="key" :label="label" :value="key" />
            </el-select>
            <el-select v-model="taskQuery.level" placeholder="等级" clearable style="width: 110px" @change="searchTasks">
              <el-option v-for="(item, key) in AI_LEVEL" :key="key" :label="item.label" :value="key" />
            </el-select>
            <el-select v-model="taskQuery.status" placeholder="状态" clearable style="width: 110px" @change="searchTasks">
              <el-option v-for="(item, key) in AI_STATUS" :key="key" :label="item.label" :value="key" />
            </el-select>
            <el-button @click="searchTasks">查询</el-button>
            <el-button text @click="resetTasks">重置</el-button>
            <span class="grow"></span>
            <span class="dim-note">共 {{ taskTotal }} 项任务</span>
          </div>

          <div class="table-wrap">
            <el-table :data="taskRows" v-loading="taskLoading" row-key="id">
              <el-table-column prop="task_name" label="任务" min-width="230" show-overflow-tooltip>
                <template #default="{ row }"><span class="strong">{{ row.task_name }}</span></template>
              </el-table-column>
              <el-table-column label="阶段" width="106">
                <template #default="{ row }"><span class="muted">{{ AI_PHASE[row.phase] }}</span></template>
              </el-table-column>
              <el-table-column label="等级" width="104">
                <template #default="{ row }"><StatusPill kind="aiLevel" :value="row.level" /></template>
              </el-table-column>
              <el-table-column prop="agent_name" label="Agent" width="140" show-overflow-tooltip />
              <el-table-column label="状态" width="92">
                <template #default="{ row }"><StatusPill kind="aiStatus" :value="row.status" /></template>
              </el-table-column>
              <el-table-column label="失效分" width="150">
                <template #default="{ row }">
                  <div class="score-bar">
                    <div class="score-track"><i :style="{ width: `${row.failure_score}%` }"></i></div>
                    <strong class="num">{{ row.failure_score }}</strong>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="判定" width="94">
                <template #default="{ row }">
                  <span class="band" :class="row.failure_band.level.toLowerCase()">{{ row.failure_band.label }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="human_minutes" label="人工分钟" width="82" align="center" />
              <el-table-column prop="retries" label="重试" width="58" align="center" />
              <el-table-column label="发生日期" width="100">
                <template #default="{ row }"><span class="muted">{{ String(row.occurred_at).slice(0, 10) }}</span></template>
              </el-table-column>
              <el-table-column v-if="isAdmin()" label="操作" width="108" fixed="right">
                <template #default="{ row }">
                  <el-button link type="primary" @click="openTaskEdit(row)">编辑</el-button>
                  <el-button link type="danger" @click="removeTask(row)">删除</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <div class="pager">
            <el-pagination
              v-model:current-page="taskQuery.page"
              v-model:page-size="taskQuery.page_size"
              :total="taskTotal"
              :page-sizes="[10, 20, 50]"
              layout="total, sizes, prev, pager, next"
              @current-change="loadTasks"
              @size-change="searchTasks"
            />
          </div>
        </el-tab-pane>

        <el-tab-pane label="缺陷与帕累托" name="defects">
          <div class="tab-body top-gap">
            <div class="grid-2">
              <div class="panel inner-panel">
                <div class="panel-head">
                  <div class="panel-title">缺陷帕累托图</div>
                  <div class="panel-note">80% 参考线 · 按累计发生次数</div>
                </div>
                <div class="chart-body">
                  <ChartPanel :option="paretoOption" :height="310" :empty="!stats" />
                </div>
              </div>
              <div class="panel inner-panel">
                <div class="panel-head">
                  <div class="panel-title">严重程度分布</div>
                  <div class="panel-note">按累计发生次数</div>
                </div>
                <div class="chart-body">
                  <ChartPanel :option="severityOption" :height="310" :empty="!stats" />
                </div>
              </div>
            </div>

            <div class="panel inner-panel">
              <div class="filter-bar">
                <el-input
                  v-model="defectQuery.q"
                  placeholder="搜索缺陷 / 分类"
                  clearable
                  style="width: 210px"
                  :prefix-icon="Search"
                  @keyup.enter="searchDefects"
                  @clear="searchDefects"
                />
                <el-select v-model="defectQuery.phase" placeholder="发现阶段" clearable style="width: 130px" @change="searchDefects">
                  <el-option v-for="(label, key) in AI_PHASE" :key="key" :label="label" :value="key" />
                </el-select>
                <el-select v-model="defectQuery.severity" placeholder="严重程度" clearable style="width: 120px" @change="searchDefects">
                  <el-option v-for="(item, key) in SEVERITY" :key="key" :label="item.label" :value="key" />
                </el-select>
                <el-select v-model="defectQuery.status" placeholder="修复状态" clearable style="width: 120px" @change="searchDefects">
                  <el-option v-for="(item, key) in DEFECT_STATUS" :key="key" :label="item.label" :value="key" />
                </el-select>
                <el-button @click="searchDefects">查询</el-button>
                <el-button text @click="resetDefects">重置</el-button>
                <span class="grow"></span>
                <el-button v-if="isAdmin()" size="small" :icon="Plus" @click="openDefectCreate">登记缺陷</el-button>
                <span class="dim-note">共 {{ defectTotal }} 条记录</span>
              </div>
              <div class="table-wrap">
                <el-table :data="defectRows" v-loading="defectLoading" row-key="id">
                  <el-table-column type="expand">
                    <template #default="{ row }">
                      <div class="defect-expand">
                        <div><span>根因</span><p>{{ row.root_cause || '未填写' }}</p></div>
                        <div><span>修复措施</span><p>{{ row.fix_action || '未填写' }}</p></div>
                      </div>
                    </template>
                  </el-table-column>
                  <el-table-column prop="title" label="缺陷" min-width="230" show-overflow-tooltip />
                  <el-table-column prop="category" label="分类" width="128" />
                  <el-table-column label="阶段" width="100">
                    <template #default="{ row }"><span class="muted">{{ AI_PHASE[row.phase] }}</span></template>
                  </el-table-column>
                  <el-table-column label="严重度" width="86">
                    <template #default="{ row }"><StatusPill kind="severity" :value="row.severity" /></template>
                  </el-table-column>
                  <el-table-column label="发生" width="66" align="center">
                    <template #default="{ row }"><span class="num">{{ row.occurrences }}</span></template>
                  </el-table-column>
                  <el-table-column label="AI 相关" width="80" align="center">
                    <template #default="{ row }">
                      <span :class="row.ai_related ? 'text-accent' : 'muted'">{{ row.ai_related ? '是' : '否' }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="状态" width="90">
                    <template #default="{ row }"><StatusPill kind="defectStatus" :value="row.status" /></template>
                  </el-table-column>
                  <el-table-column label="发现日期" width="102">
                    <template #default="{ row }"><span class="muted">{{ row.found_at }}</span></template>
                  </el-table-column>
                  <el-table-column v-if="isAdmin()" label="操作" width="108" fixed="right">
                    <template #default="{ row }">
                      <el-button link type="primary" @click="openDefectEdit(row)">编辑</el-button>
                      <el-button link type="danger" @click="removeDefect(row)">删除</el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
              <div class="pager">
                <el-pagination
                  v-model:current-page="defectQuery.page"
                  v-model:page-size="defectQuery.page_size"
                  :total="defectTotal"
                  :page-sizes="[10, 20, 50]"
                  layout="total, sizes, prev, pager, next"
                  @current-change="loadDefects"
                  @size-change="searchDefects"
                />
              </div>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="分级机制" name="grading">
          <div class="tab-body">
            <div class="level-cards">
              <div
                v-for="level in grading?.levels || []"
                :key="level.code"
                class="level-card"
                :class="level.code.toLowerCase()"
              >
                <div class="level-code">
                  <span>{{ level.code }}</span>
                  <i></i>
                </div>
                <h3>{{ level.name }}</h3>
                <p>{{ level.definition }}</p>
                <div class="level-meta">
                  <span>验收方式</span>
                  <strong>{{ level.acceptance }}</strong>
                </div>
                <div class="level-meta">
                  <span>人的职责</span>
                  <strong>{{ level.human_role }}</strong>
                </div>
              </div>
            </div>

            <div class="panel inner-panel">
              <div class="panel-head">
                <div class="panel-title">按软件工程阶段的 AI 任务拆分</div>
                <div class="panel-note">L1 自动完成 · L2 人机协作 · L3 纯人工</div>
              </div>
              <div class="grading-scroll">
                <div class="grading-matrix">
                  <div class="matrix-head">
                    <div>阶段</div>
                    <div class="head-l1">L1 Agent 自动完成</div>
                    <div class="head-l2">L2 人机协作</div>
                    <div class="head-l3">L3 纯人工</div>
                  </div>
                  <div v-for="row in grading?.table || []" :key="row.phase" class="matrix-row">
                    <div class="matrix-phase">
                      <strong>{{ row.phase_name }}</strong>
                      <span class="mono">{{ row.phase }}</span>
                    </div>
                    <div class="matrix-cell l1">
                      <span v-for="item in row.l1" :key="item" class="task-chip">{{ item }}</span>
                    </div>
                    <div class="matrix-cell l2">
                      <span v-for="item in row.l2" :key="item" class="task-chip">{{ item }}</span>
                    </div>
                    <div class="matrix-cell l3">
                      <span v-for="item in row.l3" :key="item" class="task-chip">{{ item }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="grid-2-even">
              <div class="panel inner-panel">
                <div class="panel-head">
                  <div class="panel-title">升级、降级与人工接管规则</div>
                  <div class="panel-note">与失效分联动</div>
                </div>
                <ol class="rule-list">
                  <li v-for="(rule, index) in grading?.rules || []" :key="rule">
                    <span class="rule-index num">{{ String(index + 1).padStart(2, '0') }}</span>
                    <p>{{ rule }}</p>
                  </li>
                </ol>
              </div>
              <div class="panel inner-panel">
                <div class="panel-head">
                  <div class="panel-title">评分维度说明</div>
                  <div class="panel-note">0 = 无失效，5 = 严重失效</div>
                </div>
                <div class="table-wrap">
                  <el-table :data="grading?.rubric || []" size="small">
                    <el-table-column prop="name" label="维度" width="110" />
                    <el-table-column label="权重" width="70">
                      <template #default="{ row }"><span class="num">{{ row.weight }}%</span></template>
                    </el-table-column>
                    <el-table-column prop="hint" label="观察点" min-width="230" show-overflow-tooltip />
                  </el-table>
                </div>
              </div>
            </div>

            <div class="formula-box">
              <div class="formula-label">评分与可靠性合成</div>
              <div class="formula">{{ stats?.formula || '—' }}</div>
              <div class="rule-tags">
                <span v-for="item in grading?.thresholds || []" :key="item.level" class="rule-tag" :class="item.level.toLowerCase()">
                  {{ item.min }}–{{ item.max }} {{ item.label }}
                </span>
              </div>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>

    <el-dialog
      v-model="taskDialog.visible"
      :title="taskDialog.mode === 'create' ? '登记 AI 任务' : '编辑 AI 任务'"
      width="760px"
      destroy-on-close
      append-to-body
    >
      <el-form ref="taskFormRef" :model="taskForm" :rules="taskRules" label-width="86px">
        <div class="form-grid">
          <el-form-item label="任务名称" prop="task_name" class="span-2">
            <el-input v-model="taskForm.task_name" maxlength="160" placeholder="描述 Agent 承担的具体任务" />
          </el-form-item>
          <el-form-item label="所属阶段" prop="phase">
            <el-select v-model="taskForm.phase" style="width: 100%">
              <el-option v-for="(label, key) in AI_PHASE" :key="key" :label="label" :value="key" />
            </el-select>
          </el-form-item>
          <el-form-item label="协作等级" prop="level">
            <el-select v-model="taskForm.level" style="width: 100%">
              <el-option v-for="(item, key) in AI_LEVEL" :key="key" :label="item.label" :value="key" />
            </el-select>
          </el-form-item>
          <el-form-item label="Agent" prop="agent_name">
            <el-input v-model="taskForm.agent_name" maxlength="60" placeholder="如 编码Agent" />
          </el-form-item>
          <el-form-item label="任务状态" prop="status">
            <el-select v-model="taskForm.status" style="width: 100%">
              <el-option v-for="(item, key) in AI_STATUS" :key="key" :label="item.label" :value="key" />
            </el-select>
          </el-form-item>
        </div>

        <div class="score-editor">
          <div class="score-editor-head">
            <div>
              <strong>五维失效评分</strong>
              <p>每项 0–5 分，分数越高表示失效越严重。</p>
            </div>
            <div class="score-preview" :class="scoreBand.level.toLowerCase()">
              <span>FS</span>
              <strong class="num">{{ scorePreview }}</strong>
              <em>{{ scoreBand.label }}</em>
            </div>
          </div>
          <div class="slider-grid">
            <div v-for="dim in dimensions" :key="dim.key" class="slider-row">
              <div class="slider-label">
                <span>{{ dim.name }}</span>
                <strong class="num">{{ taskForm[dim.key] }}</strong>
              </div>
              <el-slider v-model="taskForm[dim.key]" :min="0" :max="5" :step="1" show-stops />
            </div>
          </div>
          <div v-if="scorePreview >= 40" class="score-warning">
            <el-icon><Warning /></el-icon>
            失效分已达到 {{ scorePreview }}，按规则需人工复核并将协作等级上调一级。
          </div>
        </div>

        <div class="form-grid" style="margin-top: 16px">
          <el-form-item label="人工耗时">
            <el-input-number v-model="taskForm.human_minutes" :min="0" :max="100000" style="width: 100%" />
          </el-form-item>
          <el-form-item label="重试次数">
            <el-input-number v-model="taskForm.retries" :min="0" :max="100" style="width: 100%" />
          </el-form-item>
          <el-form-item label="发生日期">
            <el-date-picker
              v-model="taskForm.occurred_at"
              type="date"
              value-format="YYYY-MM-DD"
              placeholder="选择日期"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="复盘备注" class="span-2">
            <el-input
              v-model="taskForm.notes"
              type="textarea"
              :rows="3"
              maxlength="2000"
              show-word-limit
              placeholder="记录失效表现、人工修正动作与遗留风险"
            />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <div class="dialog-foot">
          <el-button @click="taskDialog.visible = false">取消</el-button>
          <el-button type="primary" :loading="taskSaving" @click="saveTask">保存任务</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="defectDialog.visible"
      :title="defectDialog.mode === 'create' ? '登记缺陷' : '编辑缺陷'"
      width="680px"
      destroy-on-close
      append-to-body
    >
      <el-form ref="defectFormRef" :model="defectForm" :rules="defectRules" label-width="88px">
        <div class="form-grid">
          <el-form-item label="缺陷标题" prop="title" class="span-2">
            <el-input v-model="defectForm.title" maxlength="160" />
          </el-form-item>
          <el-form-item label="发现阶段" prop="phase">
            <el-select v-model="defectForm.phase" style="width: 100%">
              <el-option v-for="(label, key) in AI_PHASE" :key="key" :label="label" :value="key" />
            </el-select>
          </el-form-item>
          <el-form-item label="缺陷分类" prop="category">
            <el-select v-model="defectForm.category" filterable allow-create style="width: 100%" placeholder="选择或输入分类">
              <el-option v-for="item in categoryOptions" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>
          <el-form-item label="严重程度" prop="severity">
            <el-select v-model="defectForm.severity" style="width: 100%">
              <el-option v-for="(item, key) in SEVERITY" :key="key" :label="item.label" :value="key" />
            </el-select>
          </el-form-item>
          <el-form-item label="发生次数" prop="occurrences">
            <el-input-number v-model="defectForm.occurrences" :min="1" :max="1000" style="width: 100%" />
          </el-form-item>
          <el-form-item label="修复状态">
            <el-select v-model="defectForm.status" style="width: 100%">
              <el-option v-for="(item, key) in DEFECT_STATUS" :key="key" :label="item.label" :value="key" />
            </el-select>
          </el-form-item>
          <el-form-item label="是否 AI 相关">
            <el-switch v-model="defectForm.ai_related" active-text="是" inactive-text="否" />
          </el-form-item>
          <el-form-item label="发现日期">
            <el-date-picker
              v-model="defectForm.found_at"
              type="date"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-form-item>
          <el-form-item label="根因分析" class="span-2">
            <el-input v-model="defectForm.root_cause" type="textarea" :rows="2" maxlength="2000" />
          </el-form-item>
          <el-form-item label="修复措施" class="span-2">
            <el-input v-model="defectForm.fix_action" type="textarea" :rows="2" maxlength="2000" />
          </el-form-item>
        </div>
      </el-form>
      <template #footer>
        <div class="dialog-foot">
          <el-button @click="defectDialog.visible = false">取消</el-button>
          <el-button type="primary" :loading="defectSaving" @click="saveDefect">保存缺陷</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Search, Warning } from '@element-plus/icons-vue'
import { aiApi } from '@/api'
import ChartPanel from '@/components/ChartPanel.vue'
import StatCard from '@/components/StatCard.vue'
import StatusPill from '@/components/StatusPill.vue'
import {
  AI_LEVEL,
  AI_PHASE,
  AI_STATUS,
  CHART_COLORS,
  DEFECT_STATUS,
  SEVERITY
} from '@/constants/labels'
import { isAdmin } from '@/stores/auth'

const activeTab = ref('overview')
const loading = ref(false)
const stats = ref(null)
const grading = ref(null)

const summary = computed(() => ({
  task_count: 0,
  avg_failure_score: 0,
  success_rate: 0,
  reliability: 0,
  high_failure_count: 0,
  human_minutes: 0,
  retry_count: 0,
  defect_occurrences: 0,
  ai_related_rate: 0,
  open_rate: 0,
  ...(stats.value?.summary || {})
}))

const bandOf = (score) => {
  if (score < 20) return { level: 'LOW', label: '低失效' }
  if (score < 40) return { level: 'MEDIUM', label: '中失效' }
  if (score < 60) return { level: 'HIGH', label: '高失效' }
  return { level: 'CRITICAL', label: '严重失效' }
}

const chartBase = {
  textStyle: { fontFamily: 'Microsoft YaHei' },
  tooltip: {
    backgroundColor: 'rgba(12, 34, 56, .94)',
    borderWidth: 0,
    padding: [8, 12],
    textStyle: { color: '#fff', fontSize: 11 }
  }
}

const axisCommon = {
  axisLine: { lineStyle: { color: '#e5dfd2' } },
  axisTick: { show: false },
  axisLabel: { color: '#7c878d', fontSize: 10 },
  splitLine: { lineStyle: { color: '#f1ece1', type: 'dashed' } }
}

const phaseOption = computed(() => {
  const rows = stats.value?.by_phase || []
  return {
    ...chartBase,
    grid: { left: 10, right: 24, top: 22, bottom: 8, containLabel: true },
    tooltip: {
      ...chartBase.tooltip,
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params) => {
        const item = rows[params[0].dataIndex]
        return `${item.phase_name}<br/>任务 ${item.task_count} 项<br/>平均失效分 ${item.avg_failure_score}<br/>综合可靠性 ${item.reliability}`
      }
    },
    xAxis: { type: 'value', max: 100, ...axisCommon },
    yAxis: {
      type: 'category',
      data: rows.map((item) => item.phase_name),
      ...axisCommon,
      splitLine: { show: false },
      axisLabel: { ...axisCommon.axisLabel, fontSize: 11 }
    },
    series: [
      {
        type: 'bar',
        barWidth: 14,
        showBackground: true,
        backgroundStyle: { color: '#f2eee4', borderRadius: 6 },
        label: {
          show: true,
          position: 'right',
          formatter: '{c}',
          color: '#4d5a62',
          fontSize: 10,
          fontWeight: 600
        },
        data: rows.map((item) => ({
          value: item.avg_failure_score,
          itemStyle: {
            borderRadius: 6,
            color:
              item.avg_failure_score >= 60
                ? '#a53d33'
                : item.avg_failure_score >= 40
                  ? '#c06a3c'
                  : item.avg_failure_score >= 20
                    ? '#d9a441'
                    : '#2f7d5b'
          }
        })),
        markLine: {
          silent: true,
          symbol: 'none',
          lineStyle: { type: 'dashed', color: '#c7b8a5' },
          label: { color: '#9a8f80', fontSize: 9, formatter: '{c}' },
          data: [{ xAxis: 20 }, { xAxis: 40 }, { xAxis: 60 }]
        }
      }
    ]
  }
})

const levelOption = computed(() => {
  const rows = stats.value?.level_distribution || []
  const colorMap = { L1: '#2d6a73', L2: '#d9a441', L3: '#7c6b93' }
  return {
    ...chartBase,
    tooltip: { ...chartBase.tooltip, trigger: 'item', formatter: '{b}<br/>{c} 项（{d}%）' },
    legend: {
      bottom: 0,
      left: 'center',
      itemWidth: 8,
      itemHeight: 8,
      textStyle: { color: '#6c777e', fontSize: 10 }
    },
    series: [
      {
        type: 'pie',
        radius: ['46%', '68%'],
        center: ['50%', '43%'],
        itemStyle: { borderColor: '#fffdf8', borderWidth: 3 },
        label: { show: false },
        data: rows.map((item) => ({
          name: AI_LEVEL[item.level]?.label || item.level,
          value: item.count,
          itemStyle: { color: colorMap[item.level] }
        }))
      }
    ],
    graphic: [
      {
        type: 'text',
        left: 'center',
        top: '34%',
        style: {
          text: String(summary.value.task_count),
          fill: '#0c2238',
          fontSize: 24,
          fontFamily: 'Bahnschrift',
          fontWeight: 600,
          textAlign: 'center'
        }
      },
      {
        type: 'text',
        left: 'center',
        top: '47%',
        style: { text: '任务', fill: '#8a9498', fontSize: 10, textAlign: 'center' }
      }
    ]
  }
})

const statusRows = computed(() => stats.value?.status_distribution || [])
function statusPercent(item) {
  const total = summary.value.task_count || 1
  return Math.round((item.count / total) * 100)
}

const paretoOption = computed(() => {
  const rows = stats.value?.pareto || []
  return {
    ...chartBase,
    grid: { left: 12, right: 26, top: 34, bottom: 34, containLabel: true },
    legend: {
      top: 2,
      right: 4,
      itemWidth: 10,
      itemHeight: 6,
      textStyle: { color: '#6c777e', fontSize: 10 }
    },
    tooltip: {
      ...chartBase.tooltip,
      trigger: 'axis',
      formatter: (params) => {
        const item = rows[params[0].dataIndex]
        return `${item.category}<br/>发生 ${item.occurrences} 次（${item.share}%）<br/>累计 ${item.cumulative}%`
      }
    },
    xAxis: {
      type: 'category',
      data: rows.map((item) => item.category),
      ...axisCommon,
      splitLine: { show: false },
      axisLabel: { ...axisCommon.axisLabel, interval: 0, fontSize: 9.5 }
    },
    yAxis: [
      { type: 'value', name: '次数', ...axisCommon, nameTextStyle: { color: '#9aa2a4', fontSize: 10 } },
      {
        type: 'value',
        name: '累计 %',
        min: 0,
        max: 100,
        ...axisCommon,
        splitLine: { show: false },
        nameTextStyle: { color: '#9aa2a4', fontSize: 10 }
      }
    ],
    series: [
      {
        name: '发生次数',
        type: 'bar',
        barWidth: 22,
        itemStyle: { color: '#2f6690', borderRadius: [3, 3, 0, 0] },
        label: { show: true, position: 'top', color: '#4d5a62', fontSize: 10, fontWeight: 600 },
        data: rows.map((item) => item.occurrences)
      },
      {
        name: '累计占比',
        type: 'line',
        yAxisIndex: 1,
        smooth: false,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { color: '#d9a441', width: 2 },
        itemStyle: { color: '#d9a441', borderColor: '#fffdf8', borderWidth: 2 },
        data: rows.map((item) => item.cumulative),
        markLine: {
          silent: true,
          symbol: 'none',
          lineStyle: { color: '#b6453a', type: 'dashed', width: 1 },
          label: { formatter: '80%', color: '#b6453a', fontSize: 10 },
          data: [{ yAxis: 80 }]
        }
      }
    ]
  }
})

const severityOption = computed(() => {
  const rows = stats.value?.severity_distribution || []
  const colorMap = { CRITICAL: '#a53d33', MAJOR: '#c06a3c', MINOR: '#2f6690', TRIVIAL: '#a7a093' }
  return {
    ...chartBase,
    tooltip: { ...chartBase.tooltip, trigger: 'item', formatter: '{b}<br/>{c} 次（{d}%）' },
    legend: {
      bottom: 0,
      left: 'center',
      itemWidth: 8,
      itemHeight: 8,
      textStyle: { color: '#6c777e', fontSize: 10 }
    },
    series: [
      {
        type: 'pie',
        radius: ['44%', '68%'],
        center: ['50%', '44%'],
        itemStyle: { borderColor: '#fffdf8', borderWidth: 3 },
        label: {
          show: true,
          formatter: '{b}\n{c}',
          color: '#5f6a70',
          fontSize: 10,
          lineHeight: 15
        },
        labelLine: { length: 10, length2: 8, lineStyle: { color: '#d8d0c1' } },
        data: rows.map((item) => ({
          name: SEVERITY[item.severity]?.label || item.severity,
          value: item.count,
          itemStyle: { color: colorMap[item.severity] }
        }))
      }
    ]
  }
})

const categoryOptions = computed(() => {
  const set = new Set((stats.value?.pareto || []).map((item) => item.category))
  ;['需求理解偏差', '接口契约不一致', '前端联调问题', '数据模型遗漏', '边界条件缺失', '文案与样式', '部署配置错误'].forEach(
    (item) => set.add(item)
  )
  return [...set]
})

async function loadOverview() {
  loading.value = true
  try {
    const [statsData, gradingData] = await Promise.all([aiApi.stats(), aiApi.grading()])
    stats.value = statsData
    grading.value = gradingData
  } catch {
    /* 已统一提示 */
  } finally {
    loading.value = false
  }
}

/* ---------------- AI 任务 ---------------- */
const taskLoading = ref(false)
const taskSaving = ref(false)
const taskRows = ref([])
const taskTotal = ref(0)
const taskQuery = reactive({ page: 1, page_size: 10, q: '', phase: '', level: '', status: '' })
const taskDialog = reactive({ visible: false, mode: 'create' })
const taskFormRef = ref()

const dimensions = [
  { key: 'correctness', name: '正确性 C' },
  { key: 'completeness', name: '完整性 I' },
  { key: 'runnability', name: '可运行性 R' },
  { key: 'maintainability', name: '可维护性 M' },
  { key: 'compliance', name: '合规与安全 S' }
]

const emptyTask = () => ({
  id: null,
  task_name: '',
  phase: 'IMPLEMENTATION',
  level: 'L1',
  agent_name: '编码Agent',
  status: 'SUCCESS',
  correctness: 0,
  completeness: 0,
  runnability: 0,
  maintainability: 0,
  compliance: 0,
  human_minutes: 0,
  retries: 0,
  occurred_at: new Date().toISOString().slice(0, 10),
  notes: ''
})

const taskForm = reactive(emptyTask())
const taskRules = {
  task_name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  phase: [{ required: true, message: '请选择阶段', trigger: 'change' }],
  level: [{ required: true, message: '请选择协作等级', trigger: 'change' }],
  agent_name: [{ required: true, message: '请输入 Agent 名称', trigger: 'blur' }],
  status: [{ required: true, message: '请选择任务状态', trigger: 'change' }]
}

const scorePreview = computed(() => {
  const weighted =
    25 * taskForm.correctness +
    20 * taskForm.completeness +
    25 * taskForm.runnability +
    15 * taskForm.maintainability +
    15 * taskForm.compliance
  return Math.round((weighted / 5) * 10) / 10
})

const scoreBand = computed(() => bandOf(scorePreview.value))

async function loadTasks() {
  taskLoading.value = true
  try {
    const data = await aiApi.tasks({
      page: taskQuery.page,
      page_size: taskQuery.page_size,
      q: taskQuery.q || undefined,
      phase: taskQuery.phase || undefined,
      level: taskQuery.level || undefined,
      status: taskQuery.status || undefined
    })
    taskRows.value = data.items
    taskTotal.value = data.total
  } catch {
    /* 已统一提示 */
  } finally {
    taskLoading.value = false
  }
}

function searchTasks() {
  taskQuery.page = 1
  loadTasks()
}

function resetTasks() {
  Object.assign(taskQuery, { page: 1, q: '', phase: '', level: '', status: '' })
  loadTasks()
}

function openTaskCreate() {
  Object.assign(taskForm, emptyTask())
  taskDialog.mode = 'create'
  taskDialog.visible = true
}

function openTaskEdit(row) {
  Object.assign(taskForm, {
    ...emptyTask(),
    ...row,
    occurred_at: String(row.occurred_at).slice(0, 10)
  })
  taskDialog.mode = 'edit'
  taskDialog.visible = true
}

async function saveTask() {
  if (!taskFormRef.value) return
  try {
    await taskFormRef.value.validate()
  } catch {
    return
  }
  taskSaving.value = true
  try {
    const payload = {
      task_name: taskForm.task_name,
      phase: taskForm.phase,
      level: taskForm.level,
      agent_name: taskForm.agent_name,
      status: taskForm.status,
      correctness: taskForm.correctness,
      completeness: taskForm.completeness,
      runnability: taskForm.runnability,
      maintainability: taskForm.maintainability,
      compliance: taskForm.compliance,
      human_minutes: taskForm.human_minutes,
      retries: taskForm.retries,
      occurred_at: taskForm.occurred_at || null,
      notes: taskForm.notes || ''
    }
    if (taskDialog.mode === 'create') {
      await aiApi.createTask(payload)
      ElMessage.success(`AI 任务已登记，失效分 ${scorePreview.value}`)
    } else {
      await aiApi.updateTask(taskForm.id, payload)
      ElMessage.success('AI 任务已更新并重新评分')
    }
    taskDialog.visible = false
    loadTasks()
    loadOverview()
  } catch {
    /* 已统一提示 */
  } finally {
    taskSaving.value = false
  }
}

async function removeTask(row) {
  try {
    await ElMessageBox.confirm(`确认删除 AI 任务「${row.task_name}」？`, '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }
  try {
    await aiApi.removeTask(row.id)
    ElMessage.success('AI 任务已删除')
    if (taskRows.value.length === 1 && taskQuery.page > 1) taskQuery.page -= 1
    loadTasks()
    loadOverview()
  } catch {
    /* 已统一提示 */
  }
}

/* ---------------- 缺陷 ---------------- */
const defectLoading = ref(false)
const defectSaving = ref(false)
const defectRows = ref([])
const defectTotal = ref(0)
const defectQuery = reactive({ page: 1, page_size: 10, q: '', phase: '', severity: '', status: '' })
const defectDialog = reactive({ visible: false, mode: 'create' })
const defectFormRef = ref()

const emptyDefect = () => ({
  id: null,
  title: '',
  phase: 'IMPLEMENTATION',
  category: '需求理解偏差',
  severity: 'MAJOR',
  occurrences: 1,
  ai_related: true,
  status: 'OPEN',
  found_at: new Date().toISOString().slice(0, 10),
  root_cause: '',
  fix_action: ''
})

const defectForm = reactive(emptyDefect())
const defectRules = {
  title: [{ required: true, message: '请输入缺陷标题', trigger: 'blur' }],
  phase: [{ required: true, message: '请选择发现阶段', trigger: 'change' }],
  category: [{ required: true, message: '请选择缺陷分类', trigger: 'change' }],
  severity: [{ required: true, message: '请选择严重程度', trigger: 'change' }]
}

async function loadDefects() {
  defectLoading.value = true
  try {
    const data = await aiApi.defects({
      page: defectQuery.page,
      page_size: defectQuery.page_size,
      q: defectQuery.q || undefined,
      phase: defectQuery.phase || undefined,
      severity: defectQuery.severity || undefined,
      status: defectQuery.status || undefined
    })
    defectRows.value = data.items
    defectTotal.value = data.total
  } catch {
    /* 已统一提示 */
  } finally {
    defectLoading.value = false
  }
}

function searchDefects() {
  defectQuery.page = 1
  loadDefects()
}

function resetDefects() {
  Object.assign(defectQuery, { page: 1, q: '', phase: '', severity: '', status: '' })
  loadDefects()
}

function openDefectCreate() {
  Object.assign(defectForm, emptyDefect())
  defectDialog.mode = 'create'
  defectDialog.visible = true
}

function openDefectEdit(row) {
  Object.assign(defectForm, { ...emptyDefect(), ...row })
  defectDialog.mode = 'edit'
  defectDialog.visible = true
}

async function saveDefect() {
  if (!defectFormRef.value) return
  try {
    await defectFormRef.value.validate()
  } catch {
    return
  }
  defectSaving.value = true
  try {
    const payload = {
      title: defectForm.title,
      phase: defectForm.phase,
      category: defectForm.category,
      severity: defectForm.severity,
      occurrences: defectForm.occurrences,
      ai_related: defectForm.ai_related,
      status: defectForm.status,
      found_at: defectForm.found_at || null,
      root_cause: defectForm.root_cause || '',
      fix_action: defectForm.fix_action || ''
    }
    if (defectDialog.mode === 'create') {
      await aiApi.createDefect(payload)
      ElMessage.success('缺陷已登记')
    } else {
      await aiApi.updateDefect(defectForm.id, payload)
      ElMessage.success('缺陷已更新')
    }
    defectDialog.visible = false
    loadDefects()
    loadOverview()
  } catch {
    /* 已统一提示 */
  } finally {
    defectSaving.value = false
  }
}

async function removeDefect(row) {
  try {
    await ElMessageBox.confirm(`确认删除缺陷「${row.title}」？`, '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消'
    })
  } catch {
    return
  }
  try {
    await aiApi.removeDefect(row.id)
    ElMessage.success('缺陷已删除')
    if (defectRows.value.length === 1 && defectQuery.page > 1) defectQuery.page -= 1
    loadDefects()
    loadOverview()
  } catch {
    /* 已统一提示 */
  }
}

async function loadAll() {
  await Promise.all([loadOverview(), loadTasks(), loadDefects()])
}

onMounted(loadAll)
</script>

<style scoped>
.tabs-panel {
  padding: 4px 18px 18px;
}

:deep(.el-tabs__header) {
  margin-bottom: 0;
  padding: 4px 4px 0;
}

.tab-body {
  padding-top: 18px;
}

.top-gap {
  padding-top: 18px;
}

.inner-panel {
  box-shadow: none;
  background: #fffefb;
}

.overview-kpis {
  margin-bottom: 16px;
}

.status-bars {
  padding: 0 22px 18px;
  display: grid;
  gap: 9px;
}

.status-row {
  display: grid;
  grid-template-columns: 68px minmax(0, 1fr) 30px;
  align-items: center;
  gap: 10px;
  font-size: 11px;
  color: var(--muted);
}

.status-row strong {
  text-align: right;
  color: var(--navy-800);
}

.status-track {
  height: 5px;
  border-radius: 4px;
  background: #f0ece2;
  overflow: hidden;
}

.status-track i {
  display: block;
  height: 100%;
  border-radius: 4px;
  background: #2f7d5b;
}

.status-track i.partial {
  background: #d9a441;
}

.status-track i.failed {
  background: #b6453a;
}

.score-bar {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-track {
  flex: 1;
  height: 5px;
  border-radius: 4px;
  background: #f0ece2;
  overflow: hidden;
}

.score-track i {
  display: block;
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, #d9a441, #c06a3c);
}

.score-bar strong {
  width: 28px;
  text-align: right;
  font-size: 11.5px;
  color: #4d5a62;
}

.band {
  display: inline-block;
  padding: 2px 7px;
  border-radius: 4px;
  font-size: 10.5px;
  font-weight: 600;
  color: #2b6f52;
  background: #e9f3ed;
}

.band.medium {
  color: #98631e;
  background: #fbf1dc;
}

.band.high {
  color: #a5532d;
  background: #fbece2;
}

.band.critical {
  color: #a53d33;
  background: #f9e9e6;
}

.threshold-list {
  display: grid;
  gap: 8px;
  padding: 14px 18px 18px;
}

.threshold-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 9px 12px;
  border-radius: 7px;
  border: 1px solid #e4efe8;
  background: #f4faf6;
}

.threshold-item.medium {
  border-color: #efe2c4;
  background: #fdf8ec;
}

.threshold-item.high {
  border-color: #f0d8c9;
  background: #fdf1e9;
}

.threshold-item.critical {
  border-color: #efd2cd;
  background: #fbecea;
}

.threshold-range {
  flex: 0 0 56px;
  font-size: 12px;
  font-weight: 600;
  color: var(--navy-800);
}

.threshold-item strong {
  display: block;
  font-size: 12px;
  color: var(--ink);
}

.threshold-item p {
  margin-top: 3px;
  font-size: 10.5px;
  line-height: 1.55;
  color: var(--muted);
}

.formula-box {
  margin-top: 16px;
  padding: 18px 20px;
  border-radius: 9px;
  border: 1px solid #e6dfd0;
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.04) 1px, transparent 1px) 0 0 / 22px 22px,
    linear-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px) 0 0 / 22px 22px,
    linear-gradient(115deg, var(--navy-900), var(--navy-700));
  color: #dfe9f0;
}

.formula-label {
  font-size: 10px;
  letter-spacing: 0.16em;
  color: var(--gold);
}

.formula {
  margin-top: 10px;
  font-family: "Cascadia Code", "Consolas", monospace;
  font-size: 12.5px;
  line-height: 1.8;
  color: #fff;
}

.formula-box p {
  margin-top: 9px;
  max-width: 920px;
  font-size: 11px;
  line-height: 1.8;
  color: #9fb2c1;
}

.rule-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 14px;
}

.rule-tag {
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 10.5px;
  color: #cfe6d9;
  border: 1px solid rgba(122, 180, 150, 0.35);
  background: rgba(46, 125, 91, 0.18);
}

.rule-tag.medium {
  color: #efdcb4;
  border-color: rgba(217, 164, 65, 0.35);
  background: rgba(217, 164, 65, 0.16);
}

.rule-tag.high {
  color: #f0c6ad;
  border-color: rgba(192, 106, 60, 0.4);
  background: rgba(192, 106, 60, 0.16);
}

.rule-tag.critical {
  color: #f0c0b9;
  border-color: rgba(182, 69, 58, 0.4);
  background: rgba(182, 69, 58, 0.16);
}

.defect-expand {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 22px;
  padding: 6px 26px 12px;
}

.defect-expand span {
  display: block;
  margin-bottom: 5px;
  font-size: 10px;
  letter-spacing: 0.08em;
  color: var(--accent);
}

.defect-expand p {
  font-size: 11.5px;
  line-height: 1.7;
  color: #5a666d;
}

.level-cards {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.level-card {
  position: relative;
  overflow: hidden;
  padding: 20px 20px 18px;
  border-radius: var(--radius);
  border: 1px solid var(--line);
  background: var(--card);
  box-shadow: var(--shadow);
}

.level-card::before {
  content: "";
  position: absolute;
  inset: 0 auto 0 0;
  width: 3px;
  background: #2d6a73;
}

.level-card.l2::before {
  background: #d9a441;
}

.level-card.l3::before {
  background: #7c6b93;
}

.level-code {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.level-code span {
  font-family: "Bahnschrift", sans-serif;
  font-size: 27px;
  font-weight: 600;
  color: var(--navy-900);
}

.level-code i {
  width: 42px;
  height: 1px;
  background: #cfc7b7;
}

.level-card h3 {
  margin-top: 8px;
  font-size: 14px;
  color: var(--navy-800);
  letter-spacing: 0.04em;
}

.level-card p {
  margin-top: 9px;
  min-height: 57px;
  font-size: 11.5px;
  line-height: 1.7;
  color: var(--muted);
}

.level-meta {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px dashed var(--line-soft);
}

.level-meta span {
  display: block;
  font-size: 9.5px;
  letter-spacing: 0.1em;
  color: #9aa0a0;
}

.level-meta strong {
  display: block;
  margin-top: 5px;
  font-size: 11px;
  font-weight: 500;
  line-height: 1.65;
  color: #4d5a62;
}

.grading-scroll {
  overflow-x: auto;
  padding: 4px 18px 18px;
}

.grading-matrix {
  min-width: 920px;
}

.matrix-head,
.matrix-row {
  display: grid;
  grid-template-columns: 150px repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.matrix-head {
  padding: 10px 12px;
  border-radius: 7px;
  background: #f8f4ec;
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.06em;
  color: #5c686f;
}

.matrix-head .head-l1 {
  color: #2d6a73;
}

.matrix-head .head-l2 {
  color: #a9771f;
}

.matrix-head .head-l3 {
  color: #6b5b85;
}

.matrix-row {
  padding: 14px 12px;
  border-bottom: 1px solid var(--line-soft);
}

.matrix-row:last-child {
  border-bottom: none;
}

.matrix-phase strong {
  display: block;
  font-size: 12.5px;
  color: var(--navy-800);
}

.matrix-phase span {
  display: block;
  margin-top: 4px;
  font-size: 9px;
  color: #a3a39a;
}

.matrix-cell {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  align-content: flex-start;
}

.task-chip {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 10.5px;
  line-height: 1.55;
  color: #28626b;
  background: #edf5f5;
  border: 1px solid #dcecec;
}

.matrix-cell.l2 .task-chip {
  color: #8e651f;
  background: #fcf5e6;
  border-color: #f0e2c3;
}

.matrix-cell.l3 .task-chip {
  color: #61527a;
  background: #f4f0f8;
  border-color: #e6ddef;
}

.rule-list {
  margin: 0;
  padding: 12px 20px 18px;
  list-style: none;
  display: grid;
  gap: 11px;
}

.rule-list li {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding-bottom: 10px;
  border-bottom: 1px dashed var(--line-soft);
}

.rule-list li:last-child {
  border-bottom: none;
}

.rule-index {
  flex: 0 0 24px;
  padding-top: 1px;
  font-size: 10px;
  color: var(--accent);
}

.rule-list p {
  font-size: 11.5px;
  line-height: 1.75;
  color: #4f5c64;
}

.score-editor {
  margin-top: 4px;
  padding: 15px 17px 13px;
  border-radius: 9px;
  border: 1px solid var(--line);
  background: #faf7ef;
}

.score-editor-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding-bottom: 12px;
  border-bottom: 1px dashed #e5ddcd;
}

.score-editor-head strong {
  font-size: 13px;
  color: var(--navy-800);
}

.score-editor-head p {
  margin-top: 4px;
  font-size: 10.5px;
  color: var(--muted);
}

.score-preview {
  display: flex;
  align-items: baseline;
  gap: 7px;
  padding: 7px 12px;
  border-radius: 7px;
  background: #e9f3ed;
  border: 1px solid #cfe5d9;
}

.score-preview span {
  font-size: 9px;
  color: #6c8a79;
  letter-spacing: 0.08em;
}

.score-preview strong {
  font-size: 24px;
  line-height: 1;
  color: #2b6f52;
}

.score-preview em {
  font-style: normal;
  font-size: 10px;
  color: #2b6f52;
}

.score-preview.medium {
  background: #fbf1dc;
  border-color: #efdfbc;
}

.score-preview.medium strong,
.score-preview.medium em,
.score-preview.medium span {
  color: #98631e;
}

.score-preview.high {
  background: #fbece2;
  border-color: #f0d8c9;
}

.score-preview.high strong,
.score-preview.high em,
.score-preview.high span {
  color: #a5532d;
}

.score-preview.critical {
  background: #f9e9e6;
  border-color: #eed3ce;
}

.score-preview.critical strong,
.score-preview.critical em,
.score-preview.critical span {
  color: #a53d33;
}

.slider-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 4px 26px;
  padding-top: 8px;
}

.slider-row {
  padding: 4px 0;
}

.slider-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
  color: #56636b;
}

.slider-label strong {
  color: var(--navy-800);
}

:deep(.el-slider__runway) {
  margin: 10px 0;
}

.score-warning {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  padding: 8px 11px;
  border-radius: 6px;
  font-size: 11px;
  color: #a5532d;
  background: #fdf1e9;
  border: 1px solid #f0d8c9;
}

@media (max-width: 1100px) {
  .level-cards {
    grid-template-columns: 1fr;
  }

  .level-card p {
    min-height: auto;
  }
}

@media (max-width: 760px) {
  .slider-grid {
    grid-template-columns: 1fr;
  }

  .defect-expand {
    grid-template-columns: 1fr;
  }
}
</style>
