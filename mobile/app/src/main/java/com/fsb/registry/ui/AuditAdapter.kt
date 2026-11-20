package com.fsb.registry.ui

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.fsb.registry.data.AuditLog
import com.fsb.registry.R

class AuditAdapter(
    private val onClick: (AuditLog) -> Unit,
) : RecyclerView.Adapter<AuditAdapter.VH>() {

    private val items = mutableListOf<AuditLog>()

    inner class VH(view: View) : RecyclerView.ViewHolder(view) {
        val tvAction: TextView = view.findViewById(R.id.tvAuditAction)
        val tvDetails: TextView = view.findViewById(R.id.tvAuditDetails)
        val tvMeta: TextView = view.findViewById(R.id.tvAuditMeta)

        fun bind(log: AuditLog) {
            tvAction.text = log.actionDisplay ?: log.action ?: ""
            tvDetails.text = log.details?.toString() ?: ""
            tvMeta.text = log.createdAt ?: ""
            itemView.setOnClickListener { onClick(log) }
        }
    }

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): VH {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.item_audit, parent, false)
        return VH(view)
    }

    override fun onBindViewHolder(holder: VH, position: Int) {
        holder.bind(items[position])
    }

    override fun getItemCount(): Int = items.size

    fun submit(list: List<AuditLog>) {
        items.clear()
        items.addAll(list)
        notifyDataSetChanged()
    }
}
